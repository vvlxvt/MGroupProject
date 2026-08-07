from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, FileExtensionValidator

from PIL import Image
from taggit.forms import TagField
from taggit_labels.widgets import LabelWidget

from job.models import UserQuestion, ApplicantProfile


# ====== Constants ======
IMAGE_EXTENSIONS = ("jpg", "jpeg", "png")
MIN_QUESTION_LENGTH = 10
MAX_UPLOAD_SIZE = getattr(settings, "MAX_UPLOAD_SIZE", 6 * 1024 * 1024)
ALLOWED_IMAGE_MIME_TYPES = ("image/jpeg","image/png",)

# ====== Forms ======
class UserQuestionForm(forms.ModelForm):
    contact_email = forms.EmailField(
        max_length=254,
        validators=[EmailValidator(message="Введите корректный email адрес.")],
    )
    attached_photo = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(IMAGE_EXTENSIONS)],
    )

    class Meta:
        model = UserQuestion
        fields = ("contact_email", "question_text", "attached_photo")

    def clean_question_text(self):
        text = self.cleaned_data.get("question_text", "").strip()
        if len(text) < MIN_QUESTION_LENGTH:
            raise ValidationError(
                f"Вопрос должен содержать минимум {MIN_QUESTION_LENGTH} символов."
            )
        return text


    def clean_attached_photo(self):
        photo = self.cleaned_data.get("attached_photo")

        if not photo:
            return photo

        if photo.content_type not in ALLOWED_IMAGE_MIME_TYPES:
            raise ValidationError("Недопустимый тип файла.")

        if photo.size > MAX_UPLOAD_SIZE:
            max_mb = MAX_UPLOAD_SIZE / (1024 * 1024)
            raise ValidationError(
                f"Размер изображения не должен превышать {max_mb:.0f} MB."
            )

        try:
            Image.open(photo).verify()
        except Exception:
            raise ValidationError("Файл повреждён или не является изображением.")

        return photo


class ApplicantProfileForm(forms.ModelForm):
    class Meta:
        model = ApplicantProfile
        fields = (
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
        )
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ваше имя"}),
            "surname": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ваша фамилия"}),
            "position": forms.TextInput(attrs={"class": "form-control", "placeholder": "Желаемая должность"}),
            "age": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Возраст", "min": 0}),
            "education": forms.TextInput(attrs={"class": "form-control", "placeholder": "Образование"}),
            "professional_education": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Профессиональное образование"}
            ),
            "additional_education": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Дополнительное образование", "rows": 3}
            ),
            "place_of_residence": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Место проживания"}
            ),
            "telephone_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Телефон"}
            ),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "E-mail"}),
            "ready_for_business_trip": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SearchForm(forms.Form):
    query = forms.CharField(required=False, max_length=255)


class TagsForm(forms.ModelForm):
    tags = TagField(required=False, widget=LabelWidget)


class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    to = forms.EmailField()
    comments = forms.CharField(required=False, widget=forms.Textarea)
