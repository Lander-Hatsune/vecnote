from django import forms
from .models import Document

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'content', 'content_format']

class SearchForm(forms.Form):
    query = forms.CharField(max_length=500, label='Search Sentence')