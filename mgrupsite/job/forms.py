from taggit.forms import TagField
from .models import Comment, Contact
from django import forms
from taggit_labels.widgets import LabelWidget

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'message', 'photo']  # Добавляем поле фото
        # widgets = {
        #     'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
        #     'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}),
        #     'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Your Message', 'rows': 4}),
        # }

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



