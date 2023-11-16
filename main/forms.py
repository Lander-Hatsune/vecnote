from django import forms
from .models import Document


class DocumentForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={"class": "input"}))
    content = forms.CharField(widget=forms.Textarea(attrs={"class": "textarea"}))

    class Meta:
        model = Document
        fields = ["title", "content", "content_format", "do_embed", "check_todo"]

    def clean(self):
        cleaned_data = self.cleaned_data
        check_todo = cleaned_data.get("check_todo")
        if check_todo:
            if cleaned_data.get("do_embed"):
                raise forms.ValidationError("We do not embed TODO files, for saving.")
            if cleaned_data.get("content_format") != "org":
                raise forms.ValidationError(
                    "Only support TODO files in org-mode format"
                )
        return cleaned_data


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
