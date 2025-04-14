from taggit.forms import TagField
from django import forms
from taggit_labels.widgets import LabelWidget

from job.models import UserProfile, UserQuestion


class SearchForm(forms.Form):
    query = forms.CharField()


class TagsForm(forms.ModelForm):
    tags = TagField(required=False, widget=LabelWidget)


class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    to = forms.EmailField()
    comments = forms.CharField(required=False, widget=forms.Textarea)


class UserQuestionForm(forms.ModelForm):
    class Meta:
        model = UserQuestion
        fields = ["question_text", "attached_photo"]


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["email", "city"]
