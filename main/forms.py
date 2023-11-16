from django import forms
from .models import Document


class DocumentForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={"class": "input"}))
    content = forms.CharField(widget=forms.Textarea(attrs={"class": "textarea"}))

    class Meta:
        model = Document
        fields = ["title", "content", "content_format", "do_embed"]


class SearchForm(forms.Form):
    query = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={"class": "input"}),
        label="",
    )
    query_type = forms.ChoiceField(
        choices=[("vector", "Vector embedding"), ("text", "Full text")],
        label="",
    )
