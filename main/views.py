from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.models import BaseModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    View,
)
from django.utils import timezone
from django.urls import reverse_lazy
from pgvector.django import CosineDistance
from django.db.models import Q, F, Count

from .models import Document, TodoItem
from .forms import DocumentForm, SearchForm
from taggit.models import Tag

import re
import logging
import zhipuai
import orgparse as op
import datetime as dt
import subprocess
from vecnote.secret import API_KEY

zhipuai.api_key = API_KEY
log = logging.getLogger(__name__)


def embed(s):
    resp = zhipuai.model_api.invoke(
        model="text_embedding",
        prompt=s,
    )
    embed = resp.get("data").get("embedding")

    if resp.get("code") != 200:
        log.error(f"embedding fetch failed!, {resp}")
    return embed


def check_todo(content, document):
    org = op.loads(content)
    nodes = org.env.nodes[1:]
    todos = []

    def urge_color(timediff):
        if timediff <= dt.timedelta(days=1):
            return "has-background-danger-light"
        if timediff <= dt.timedelta(days=7):
            return "has-background-warning-light"
        
    def clean_str(s):
        return re.sub('[^A-Za-z0-9\.\w]+', '-', s).lower()

    for idx, node in enumerate(nodes):
        if node.todo == "TODO":
            timediff = node.deadline.start - dt.datetime.now().date()
            todos.append(
                {
                    "in_day": timediff.days,
                    "deadline": node.deadline.start,
                    "title": node.heading,
                    "tags": "; ".join(node.tags),
                    "document": document,
                    "node_idx": idx,
                    "css_class": urge_color(timediff),
                    "cleaned_title": clean_str(node.heading),
                }
            )
    return todos


class LoginRequired(LoginRequiredMixin):
    login_url = "/admin/"


class HomeView(LoginRequired, ListView):
    model = Document
    template_name = "home.html"
    context_object_name = "documents"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["documents"] = {
            "recent": Document.objects.filter(is_trashed=False)[:10],
            "pinned": Document.objects.filter(is_pinned=True).order_by("-pinned_at"),
        }
        return context


class DocumentListView(LoginRequired, ListView):
    model = Document
    template_name = "document_list.html"
    context_object_name = "documents"
    paginate_by = 50

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = context['page_obj']
        context["elided_page_range"] = page.paginator.get_elided_page_range(page.number, on_ends=1)
        return context

    def get_queryset(self):
        return Document.objects.filter(is_trashed=False)


class TrashbinView(LoginRequired, ListView):
    model = Document
    template_name = "trashbin.html"
    context_object_name = "trashed_documents"

    def get_queryset(self):
        return Document.objects.filter(is_trashed=True).order_by("-trashed_at")


class DocumentDetailView(LoginRequired, DetailView):
    model = Document
    template_name = "document_detail.html"
    context_object_name = "document"


class CreateEditBaseView:
    model = Document
    form_class = DocumentForm

    def get_success_url(self):
        return reverse_lazy("detail", args=[self.object.pk])

    def form_valid(self, form):
        iformat = form.instance.content_format
        form.instance.html_content = subprocess.check_output(
            ["pandoc", "--from", iformat, "--to", "html", "--number-sections"],
            input=form.instance.content,
            text=True,
        )
        form.instance.md_content = subprocess.check_output(
            ["pandoc", "--from", iformat, "--to", "markdown"],
            input=form.instance.content,
            text=True,
        )
        if form.instance.do_embed:
            form.instance.embedding = embed(
                form.instance.title + ":" + form.instance.md_content
            )

        form.instance.modified_at = timezone.now()
        return super().form_valid(form)


class CreateDocumentView(LoginRequired, CreateEditBaseView, CreateView):
    template_name = "document_create_form.html"


class EditDocumentView(LoginRequired, CreateEditBaseView, UpdateView):
    template_name = "document_edit_form.html"


class DeleteDocumentView(LoginRequired, View):
    template_name = "document_delete.html"
    context_object_name = "document"

    def get(self, request, pk):
        document = Document.objects.get(pk=pk)
        return render(request, self.template_name, {"document": document})

    def post(self, _, pk):
        document = Document.objects.get(pk=pk)
        if document.is_trashed:
            document.delete()
        else:
            document.is_trashed = True
            document.trashed_at = timezone.now()
            document.save()

        return HttpResponseRedirect(reverse_lazy("list"))


class RestoreDocumentView(LoginRequired, UpdateView):
    model = Document
    template_name = "document_restore.html"
    fields = ["is_trashed"]
    success_url = reverse_lazy("trashbin")

    def form_valid(self, form):
        form.instance.is_deleted = False
        form.instance.save()
        return super().form_valid(form)


class PinDocumentView(LoginRequired, UpdateView):
    model = Document
    template_name = "document_pin.html"
    context_object_name = "document"
    fields = ["is_pinned"]
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        form.instance.is_pinned = True
        form.instance.save()
        return super().form_valid(form)


class UnpinDocumentView(LoginRequired, UpdateView):
    model = Document
    template_name = "document_unpin.html"
    fields = ["is_pinned"]
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        form.instance.is_pinned = False
        form.instance.save()
        return super().form_valid(form)


class SearchView(LoginRequired, View):
    template_name = "search_form.html"

    def get(self, request):
        form = SearchForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = SearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data["query"]
            query_type = form.cleaned_data["query_type"]
            if query_type == "vector":
                search_vector = embed(query)
                results = Document.objects.order_by(
                    CosineDistance("embedding", search_vector)
                ).annotate(similarity=1 - CosineDistance("embedding", search_vector))
            else:
                results = Document.objects.filter(
                    Q(title__icontains=query) | Q(content__icontains=query)
                )
            return render(
                request, self.template_name, {"form": form, "results": results}
            )
        return render(request, self.template_name, {"form": form})


class TodosView(LoginRequired, ListView):
    model = TodoItem
    template_name = "todos.html"
    context_object_name = "todos"

    def get_queryset(self):
        TodoItem.objects.all().delete()
        for d in Document.objects.filter(check_todo=True):
            todos = check_todo(d.content, d)
            for todo in todos:
                TodoItem.objects.create(**todo)
        return TodoItem.objects.order_by("in_day")


class UpdateTodoItemView(LoginRequired, UpdateView):

    model = TodoItem
    template_name = "todoitem_update.html"
    fields = []
    success_url = reverse_lazy("todos")
    
    def form_valid(self, form):
        todo_item: TodoItem = form.instance
        document = todo_item.document

        org = op.loads(document.content)
        node: op.OrgNode = org.env.nodes[1 + todo_item.node_idx]
        linum = node.linenumber - 1

        lines = document.content.split("\n")
        cur_time_str = dt.datetime.now().strftime("%Y-%m-%d %a %H:%M")
        if not node.deadline._repeater: # change to DONE
            lines[linum] = lines[linum].replace("TODO", "DONE")
            lines[linum + 1] = f"CLOSED: [{cur_time_str}]" + lines[linum + 1]
        else: # shift to next deadline
            cur_ddl = node.deadline.start
            cur_ddl_str = cur_ddl.strftime("%Y-%m-%d %a")
            repeater = node.deadline._repeater
            if repeater[-1] == "w":
                repeat_delta = dt.timedelta(weeks=repeater[-2])
            elif repeater[-1] == "m":
                repeat_delta = dt.timedelta(days=repeater[-2] * 30)
            elif repeater[-1] == "y":
                repeat_delta = dt.timedelta(days=repeater[-2] * 365)
            next_ddl = cur_ddl + repeat_delta
            next_ddl_str = next_ddl.strftime("%Y-%m-%d %a")
            lines[linum + 1] = lines[linum + 1].replace(cur_ddl_str, next_ddl_str)
            lines.insert(linum + 2, f'- State "DONE"       from "TODO"       [{cur_time_str}]')
            pass
        document.content = "\n".join(lines)
        document.save()
        return super().form_valid(form)
            

class TagListView(LoginRequired, ListView):
    model = Tag
    template_name = "tag_list.html"
    context_object_name = "tags"

    def get_queryset(self):
        return Tag.objects.filter(document__is_trashed=False).annotate(cnt=Count("document"))


class TagDetailView(LoginRequired, DetailView):
    model = Tag
    template_name = "tag_detail.html"
    context_object_name = "tag"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag = self.get_object()
        context['documents'] = Document.objects.filter(is_trashed=False, tags__name__in=[tag]).distinct()
        return context
