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
from django.db.models import Q

from .models import Document
from .forms import DocumentForm, SearchForm

import logging
import zhipuai
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


class LoginRequired(LoginRequiredMixin):
    login_url = "/admin/"

class HomeView(LoginRequired, ListView):
    model = Document
    template_name = "home.html"
    context_object_name = "documents"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["documents"] = {
            "recent": Document.objects.filter(is_trashed=False).order_by("-modified_at")[:10],
            "pinned": Document.objects.filter(is_pinned=True).order_by("-pinned_at"),
        }
        print(context["documents"])
        return context

class DocumentListView(LoginRequired, ListView):
    model = Document
    template_name = "document_list.html"
    context_object_name = "documents"

    def get_queryset(self):
        return Document.objects.filter(is_trashed=False).order_by("-modified_at")


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
            ["pandoc", "--from", iformat, "--to", "html"],
            input=form.instance.content,
            text=True,
        )
        form.instance.md_content = subprocess.check_output(
            ["pandoc", "--from", iformat, "--to", "markdown"],
            input=form.instance.content,
            text=True,
        )

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
