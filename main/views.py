from django.forms.models import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import ListView, CreateView, DetailView, UpdateView, View
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from pgvector.django import CosineDistance

from .models import Document
from .forms import DocumentForm, SearchForm
from .serializers import DocumentSerializer

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
        return super().form_valid(form)


class DocumentDetailView(DetailView):
    model = Document
    template_name = "document_detail.html"
    context_object_name = "document"


class EditDocumentView(CreateDocumentView, UpdateView):
    template_name = "document_edit_form.html"
    pass


class SearchView(View):
    template_name = "search_results.html"

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
            ).annotate(similarity=CosineDistance("embedding", search_vector))

            return render(
                request, self.template_name, {"form": form, "results": results}
            )
        return render(request, self.template_name, {"form": form})
