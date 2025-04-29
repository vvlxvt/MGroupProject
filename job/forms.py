from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, FileExtensionValidator

from job.models import UserProfile, UserQuestion

from taggit.forms import TagField
from taggit_labels.widgets import LabelWidget


class UserQuestionForm(forms.ModelForm):
    attached_photo = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )

    class Meta:
        model = UserQuestion
        fields = ["question_text", "attached_photo"]

    def clean_question_text(self):
        text = self.cleaned_data.get('question_text')
        if text and len(text.strip()) < 10:
            raise ValidationError("Вопрос должен содержать минимум 10 символов.")
        return text

    def clean_attached_photo(self):
        photo = self.cleaned_data.get('attached_photo')
        if photo:
            max_size = 10 * 1024 * 1024  # 10MB, например
            if photo.size > max_size:
                raise ValidationError(f"Размер изображения не должен превышать {max_size / (1024 * 1024)}MB.")
        return photo


class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(
        validators=[EmailValidator(message="Введите корректный email адрес.")]
    )

    class Meta:
        model = UserProfile
        fields = ["email", "city"]

    def clean_city(self):
        city = self.cleaned_data.get('city')
        if city and any(char.isdigit() for char in city):
            raise ValidationError("Название города не должно содержать цифр.")
        return city


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
    attached_photo = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )

    class Meta:
        model = UserQuestion
        fields = ["question_text", "attached_photo"]

    def clean_question_text(self):
        text = self.cleaned_data.get('question_text')
        if text and len(text.strip()) < 10:
            raise ValidationError("Вопрос должен содержать минимум 10 символов.")
        return text

    def clean_attached_photo(self):
        photo = self.cleaned_data.get('attached_photo')
        if photo:
            max_size = settings.MAX_UPLOAD_SIZE
            if photo.size > max_size:
                raise ValidationError(f"Размер изображения не должен превышать {max_size / (1024 * 1024)}MB.")
        return photo


class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(
        validators=[EmailValidator(message="Введите корректный email адрес.")]
    )

    class Meta:
        model = UserProfile
        fields = ["email", "city"]

    def clean_city(self):
        city = self.cleaned_data.get('city')
        if city and any(char.isdigit() for char in city):
            raise ValidationError("Название города не должно содержать цифр.")
        return city

