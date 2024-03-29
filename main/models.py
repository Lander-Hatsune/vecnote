from django import forms
from django.db import models
from pgvector.django import VectorField
from taggit.managers import TaggableManager


class Document(models.Model):
    class Meta:
        ordering = ("-modified_at",)

    title = models.CharField(max_length=255)
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

    tags = TaggableManager(help_text="", blank=True)

    def __str__(self):
        return f"Document{{self.title}}"


class TodoItem(models.Model):
    in_day = models.IntegerField()
    deadline = models.DateTimeField()
    title = models.CharField(max_length=255)
    tags = models.CharField(max_length=255)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    css_class = models.CharField(max_length=50, null=True)
    node_idx = models.IntegerField()
    cleaned_title = models.CharField(max_length=255)

    def __str__(self):
        return f"TodoItem{{self.title}}"
