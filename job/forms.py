from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, FileExtensionValidator
from taggit.forms import TagField
from taggit_labels.widgets import LabelWidget

from job.models import UserProfile, UserQuestion, ApplicantProfile


class UserQuestionForm(forms.ModelForm):
    attached_photo = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png"])],
    )

    class Meta:
        model = UserQuestion
        fields = ["question_text", "attached_photo"]

    def clean_question_text(self):
        text = self.cleaned_data.get("question_text")
        if text and len(text.strip()) < 10:
            raise ValidationError("Вопрос должен содержать минимум 10 символов.")
        return text

    def clean_attached_photo(self):
        photo = self.cleaned_data.get("attached_photo")
        if photo:
            max_size = 10 * 1024 * 1024  # 10MB, например
            if photo.size > max_size:
                raise ValidationError(
                    f"Размер изображения не должен превышать {max_size / (1024 * 1024)}MB."
                )
        return photo


class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(
        validators=[EmailValidator(message="Введите корректный email адрес.")]
    )

    class Meta:
        model = UserProfile
        fields = ["email", "city"]

    def clean_city(self):
        city = self.cleaned_data.get("city")
        if city and any(char.isdigit() for char in city):
            raise ValidationError("Название города не должно содержать цифр.")
        return city


class ApplicantProfileForm(forms.ModelForm):
    class Meta:
        model = ApplicantProfile
        fields = [
            "name",
            "surname",
            "position",
            "age",
            "education",
            "professional_education",
            "additional_education",
            "place_of_residence",
            "ready_for_business_trip",
            "telephone_number",
            "email",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ваше имя",
            }),
            "surname": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ваша фамилия",
            }),
            "position": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Желаемая должность",
            }),
            "age": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Возраст",
                "min": "0",
            }),
            "education": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Образование",
            }),
            "professional_education": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Профессиональное образование",
            }),
            "additional_education": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Дополнительное образование",
                "rows": 3,
            }),
            "place_of_residence": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Место проживания",
            }),
            "telephone_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Телефон",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "E-mail",
            }),
            "ready_for_business_trip": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }


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
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png"])],
    )

    class Meta:
        model = UserQuestion
        fields = ["question_text", "attached_photo"]

    def clean_question_text(self):
        text = self.cleaned_data.get("question_text")
        if text and len(text.strip()) < 10:
            raise ValidationError("Вопрос должен содержать минимум 10 символов.")
        return text

    def clean_attached_photo(self):
        photo = self.cleaned_data.get("attached_photo")
        if photo:
            max_size = settings.MAX_UPLOAD_SIZE
            if photo.size > max_size:
                raise ValidationError(
                    f"Размер изображения не должен превышать {max_size / (1024 * 1024)}MB."
                )
        return photo


class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(
        validators=[EmailValidator(message="Введите корректный email адрес.")]
    )

    class Meta:
        model = UserProfile
        fields = ["email", "city"]

    def clean_city(self):
        city = self.cleaned_data.get("city")
        if city and any(char.isdigit() for char in city):
            raise ValidationError("Название города не должно содержать цифр.")
        return city
