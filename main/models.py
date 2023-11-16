from django import forms
from django.db import models
from pgvector.django import VectorField

# Create your models here.


class Document(models.Model):
    title = models.CharField(max_length=500)
    content = models.TextField()
    content_format = models.CharField(
        max_length=20,
        choices=[
            ("markdown", "Markdown"),
            ("org", "Org-mode"),
            ("latex", "LaTeX"),
            ("typst", "Typst"),
        ],
        default="org",
    )
    md_content = models.TextField(editable=False)
    html_content = models.TextField(editable=False)

    check_todo = models.BooleanField(default=False)

    do_embed = models.BooleanField(default=True)
    embedding = VectorField(dimensions=1024, null=True, blank=True)

    created_at = models.DateField(auto_now_add=True)
    modified_at = models.DateTimeField(editable=False)

    is_trashed = models.BooleanField(default=False)
    trashed_at = models.DateTimeField(editable=False, null=True, blank=True)

    is_pinned = models.BooleanField(default=False)
    pinned_at = models.DateTimeField(editable=False, null=True, blank=True)

    def clean(self):
        cleaned_data = super().clean()
        check_todo = cleaned_data.get("check_todo")
        if check_todo:
            if cleaned_data.get("do_embed"):
                raise forms.ValidationError(
                    "We do not embed TODO files, for saving."
                )
            if cleaned_data.get("content_format") != "org":
                raise forms.ValidationError(
                    "Only support TODO files in org-mode format"
                )
        return cleaned_data

    def __str__(self):
        return f"Document{{self.title}}"
