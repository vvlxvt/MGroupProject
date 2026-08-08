from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.validators import EmailValidator, FileExtensionValidator

from io import BytesIO
import re
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError
from taggit.forms import TagField
from taggit_labels.widgets import LabelWidget

from job.models import UserQuestion, ApplicantProfile


# ====== Constants ======
IMAGE_EXTENSIONS = ("jpg", "jpeg", "png")
MIN_QUESTION_LENGTH = 10
MAX_QUESTION_LENGTH = 3000
MAX_UPLOAD_SIZE = getattr(settings, "MAX_UPLOAD_SIZE", 6 * 1024 * 1024)
ALLOWED_IMAGE_MIME_TYPES = ("image/jpeg","image/png",)
MAX_IMAGE_PIXELS = 20_000_000

# ====== Forms ======
class UserQuestionForm(forms.ModelForm):
    personal_data_consent = forms.BooleanField(
        required=True,
        error_messages={"required": "Подтвердите согласие на обработку персональных данных."},
    )
    contact_email = forms.EmailField(
        max_length=254,
        validators=[EmailValidator(message="Введите корректный email адрес.")],
    )
    attached_photo = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(IMAGE_EXTENSIONS)],
    )
    website = forms.CharField(required=False)

    class Meta:
        model = UserQuestion
        fields = ("contact_email", "question_text", "attached_photo")

    def clean_question_text(self):
        text = self.cleaned_data.get("question_text", "").strip()
        if len(text) < MIN_QUESTION_LENGTH:
            raise ValidationError(
                f"Вопрос должен содержать минимум {MIN_QUESTION_LENGTH} символов."
            )
        if len(text) > MAX_QUESTION_LENGTH:
            raise ValidationError(
                f"Вопрос не должен превышать {MAX_QUESTION_LENGTH} символов."
            )
        return text

    def clean_contact_email(self):
        return self.cleaned_data["contact_email"].strip().lower()

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise ValidationError("Spam detected")
        return ""


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
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                image = Image.open(photo)
                image_format = image.format
                width, height = image.size
                if width * height > MAX_IMAGE_PIXELS:
                    raise ValidationError("Слишком большое разрешение изображения.")
                image.verify()
                photo.seek(0)
                image = Image.open(photo)
                image = ImageOps.exif_transpose(image)
                if image_format == "JPEG" and image.mode not in ("RGB", "L"):
                    image = image.convert("RGB")

                output = BytesIO()
                save_options = {"quality": 90, "optimize": True} if image_format == "JPEG" else {"optimize": True}
                image.save(output, format=image_format, **save_options)
                output.seek(0)
                if output.getbuffer().nbytes > MAX_UPLOAD_SIZE:
                    raise ValidationError("Обработанное изображение слишком большое.")
        except ValidationError:
            raise
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            raise ValidationError("Файл повреждён или не является изображением.")

        return InMemoryUploadedFile(
            output,
            field_name="attached_photo",
            name=photo.name,
            content_type=photo.content_type,
            size=output.getbuffer().nbytes,
            charset=None,
        )


class ApplicantProfileForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)
    personal_data_consent = forms.BooleanField(
        required=True,
        error_messages={"required": "Подтвердите согласие на обработку персональных данных."},
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = ApplicantProfile
        fields = (
            "name",
            "position",
            "experience",
            "ready_for_business_trip",
            "telephone_number",
            "email",
        )
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ваше имя"}),
            "position": forms.TextInput(attrs={"class": "form-control", "placeholder": "Желаемая должность"}),
            "experience": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Коротко об опыте работы", "rows": 4}
            ),
            "telephone_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Телефон"}
            ),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "E-mail"}),
            "ready_for_business_trip": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_email(self):
        return self.cleaned_data.get("email", "").strip().lower()

    def clean_telephone_number(self):
        phone = self.cleaned_data.get("telephone_number", "").strip()
        if phone and (not re.fullmatch(r"[+\d\s()\-]+", phone) or len(re.sub(r"\D", "", phone)) < 7):
            raise ValidationError("Введите корректный номер телефона.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("telephone_number") and not cleaned_data.get("email"):
            raise ValidationError("Укажите телефон или email для связи.")
        return cleaned_data


class SearchForm(forms.Form):
    query = forms.CharField(required=False, max_length=255)


class TagsForm(forms.ModelForm):
    tags = TagField(required=False, widget=LabelWidget)


class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    to = forms.EmailField()
    comments = forms.CharField(required=False, widget=forms.Textarea)
