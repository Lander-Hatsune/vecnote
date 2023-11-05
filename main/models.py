from django.db import models
from pgvector.django import VectorField

# Create your models here.

class Document(models.Model):
    title = models.CharField(max_length=500)
    content = models.TextField()
    html_content = models.TextField()
    embedding = VectorField(dimensions=1024)
    created_at = models.DateField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Document{{self.title}}"