from typing import Any
from django.http import HttpResponseRedirect
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


class DocumentListView(ListView):
    model = Document
    template_name = "document_list.html"
    context_object_name = "documents"
    def get_queryset(self):
        return Document.objects.filter(is_trashed=False)
     
class TrashbinView(ListView):
    model = Document
    template_name = 'trashbin.html'
    context_object_name = "trashed_documents"
    def get_queryset(self):
        return Document.objects.filter(is_trashed=True)

class CreateDocumentView(CreateView):
    model = Document
    form_class = DocumentForm
    template_name = "document_create_form.html"

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


class DocumentDetailView(DetailView):
    model = Document
    template_name = "document_detail.html"
    context_object_name = "document"


class EditDocumentView(CreateDocumentView, UpdateView):
    template_name = "document_edit_form.html"
    pass

class DeleteDocumentView(View):
    template_name = 'document_delete.html'
    context_object_name = "document"

    def get(self, request, pk):
        document = Document.objects.get(pk=pk)
        return render(request, self.template_name, {'document': document})

    def post(self, request, pk):
        document = Document.objects.get(pk=pk)
        if document.is_trashed:
            document.delete()
        else:
            document.is_trashed = True
            document.trashed_at = timezone.now()
            document.save()

        return HttpResponseRedirect(reverse_lazy('list'))

    
class RestoreDocumentView(UpdateView):
    model = Document
    template_name = 'document_restore.html'
    fields = ['is_trashed']
    success_url = reverse_lazy('trashbin')

    def form_valid(self, form):
        form.instance.is_deleted = False
        form.instance.save()
        return super().form_valid(form)


class SearchView(View):
    template_name = "search_form.html"

    def get(self, request):
        form = SearchForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = SearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data["query"]
            search_vector = embed(query)
            results = Document.objects.order_by(
                CosineDistance("embedding", search_vector)
            ).annotate(similarity=1 - CosineDistance("embedding", search_vector))

            return render(
                request, self.template_name, {"form": form, "results": results}
            )
        return render(request, self.template_name, {"form": form})
