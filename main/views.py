from django.shortcuts import render
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .models import Document
from .forms import DocumentForm
from .serializers import DocumentSerializer

import zhipuai
import subprocess
from vecnote.secret import API_KEY

zhipuai.api_key = API_KEY


@api_view(["POST"])
def create_document(request):
    org_content = request.data.get("content")
    title = request.data.get("title")

    # Convert Org-mode to HTML using Pandoc
    html_content = subprocess.check_output(
        ["pandoc", "--to", "html"], input=org_content, text=True
    )

    # Post an embedding request to the API
    embedding_response = zhipuai.model_api.invoke(
        model="text_embedding",
        prompt=org_content,
    )
    embeddings = embedding_response.get("data").get("embedding")

    print("embedding resp:", embedding_response)

    if embedding_response.get("code") != 200:
        return Response(
            {"error": "Failed to get embeddings from the API"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    document_data = {
        "title": title,
        "content": org_content,
        "html_content": html_content,
        "embedding": embeddings,
    }

    # document = Document(**document_data)
    serializer = DocumentSerializer(data=document_data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    print("invalid", document_data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentListView(ListView):
    model = Document
    template_name = "document_list.html"
    context_object_name = "documents"


class CreateDocumentView(CreateView):
    model = Document
    form_class = DocumentForm
    template_name = "document_form.html"
    success_url = reverse_lazy("document-list")
