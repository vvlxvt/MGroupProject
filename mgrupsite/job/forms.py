from taggit.forms import TagField
from .models import Comment
from django import forms
from taggit_labels.widgets import LabelWidget


class SearchForm(forms.Form):
    query = forms.CharField()

class TagsForm(forms.ModelForm):
    tags = TagField(required=False, widget=LabelWidget)


class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    to = forms.EmailField()
    comments = forms.CharField(required=False, widget=forms.Textarea)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name','email','body']



