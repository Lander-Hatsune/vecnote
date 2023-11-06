from django.forms.models import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .models import Document
from .forms import DocumentForm
from .serializers import DocumentSerializer

import logging
import zhipuai
import subprocess
from vecnote.secret import API_KEY

zhipuai.api_key = API_KEY
log = logging.getLogger(__name__)


class DocumentListView(ListView):
    model = Document
    template_name = "document_list.html"
    context_object_name = "documents"


class CreateDocumentView(CreateView):
    model = Document
    form_class = DocumentForm
    template_name = "document_form.html"

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
        # Post an embedding request to the API
        embedding_response = zhipuai.model_api.invoke(
            model="text_embedding",
            prompt=form.instance.title + ":" + form.instance.md_content,
        )
        form.instance.embedding = embedding_response.get("data").get("embedding")

        if embedding_response.get("code") != 200:
            log.error(f"embedding fetch failed!, {embedding_response}")
        return super().form_valid(form)


class DocumentDetailView(DetailView):
    model = Document
    template_name = "document_detail.html"
    context_object_name = "document"


class EditDocumentView(CreateDocumentView, UpdateView):
    pass
