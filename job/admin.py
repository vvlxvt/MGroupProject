from django.contrib import admin, messages
from django.forms import ModelForm
from django.utils.html import format_html

from .forms import TagsForm
from .models import (Article, Category, Photo, Post, PostArticle, Project,
                     UserQuestion, ApplicantProfile)


class PostArticleInline(admin.TabularInline):
    model = PostArticle
    extra = 1  # Количество пустых строк для добавления новых связей


@admin.register(Post)
class JobAdmin(admin.ModelAdmin):
    form = TagsForm
    fields = [
        ("title", "slug"),
        ("author", "status"),
        "number",
        "body",
        "tags",
        "cat",
        "photo",
    ]
    list_display = [
        "number",
        "title",
        "author",
        "updated",
        "status",
        "cat",
    ]
    list_display_links = ("number", "title")
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ["status", "publish", "author"]
    search_fields = ["title", "body"]
    raw_id_fields = ["author"]
    date_hierarchy = "publish"
    ordering = ["status", "number", "publish"]
    actions = ["set_published", "set_draft"]
    inlines = [PostArticleInline]  # Вставляем связь через промежуточную модель

    @admin.action(description="Опубликовать выбранные записи")
    # добавляем действие к выбранным записям в админку
    def set_published(self, request, queryset):
        count = queryset.update(status=Post.Status.PUBLISHED)
        self.message_user(request, f"Изменено {count} записей")

    @admin.action(description="Снять с публикации выбранные записи")
    def set_draft(self, request, queryset):
        count = queryset.update(status=Post.Status.DRAFT)
        self.message_user(
            request, f"{count} записей снято с публикации", messages.WARNING
        )


@admin.register(Article)
class CommentAdmin(admin.ModelAdmin):
    fields = [
        ("title", "slug"),
        "body",
        "photo",
    ]
    list_display = [
        "title",
        "publish",
    ]
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ["publish"]
    search_fields = ["title", "body"]
    ordering = ["publish"]


class PhotoForm(ModelForm):
    class Meta:
        model = Photo
        fields = ["image"]


class PhotoInline(admin.TabularInline):
    model = Photo
    form = PhotoForm
    extra = 1
    readonly_fields = ("thumbnail_preview",)

    def thumbnail_preview(self, instance):
        if instance.image:
            return format_html(
                '<img src="{}" width="50" height="50"/>', instance.thumbnail.url
            )
        return "Нет фото"

    thumbnail_preview.short_description = "Миниатюра"


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    fields = [("title", "slug"), ("lat", "lng"), "body", "services"]
    list_display = ["title", "publish", "lat", "lng"]
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ["publish"]
    search_fields = ["title", "body"]
    ordering = ["publish"]
    filter_horizontal = ["services"]
    inlines = [PhotoInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    fields = ["number", ("name", "slug")]
    prepopulated_fields = {"slug": ("name",)}
    list_display = (
        "number",
        "name",
    )
    list_display_links = ("number", "name")
    ordering = ["number"]


@admin.register(UserQuestion)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["contact_email", "question_text", "telegram_status", "created_at", "thumbnail"]
    list_filter = ["telegram_status", "created_at"]
    ordering = ["-created_at"]

    def thumbnail(self, obj):
        if obj.attached_photo:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover;"/>'
                "</a>",
                obj.attached_photo.url,
                obj.attached_photo.url,
            )
        return "Нет фото"

    thumbnail.short_description = "Фото"


@admin.register(ApplicantProfile)
class ApplicantProfileAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "position",
        "ready_for_business_trip",
        "telephone_number",
        "email",
        "telegram_status",
        "created_at",
    ]
    search_fields = [
        "name",
        "position",
        "experience",
        "email",
        "telephone_number",
    ]
    list_filter = ["telegram_status", "ready_for_business_trip", "created_at"]
    ordering = ["-created_at"]

