from django.contrib import admin, messages
from django.forms import ModelForm
from .forms import TagsForm
from .models import Post, Article, Project, Category, Photo, Contact, PostArticle
from django.utils.html import format_html


class PostArticleInline(admin.TabularInline):
    model = PostArticle
    extra = 1  # Количество пустых строк для добавления новых связей

@admin.register(Post)
class JobAdmin(admin.ModelAdmin):
    form = TagsForm
    fields = [("title", 'slug'),("author","status"), "body","summary", 'tags',"cat", "photo"]
    list_display = ['title', 'author', 'publish', 'status',"cat",'tags',]
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ['status', 'publish', 'author']
    search_fields = ['title', 'body']
    raw_id_fields = ['author']
    date_hierarchy = 'publish'
    ordering = ['status', 'publish']
    actions = ['set_published', 'set_draft']
    inlines = [PostArticleInline]  # Вставляем связь через промежуточную модель

    @admin.action(description='Опубликовать выбранные записи')
    # добавляем действие к выбранным записям в админку
    def set_published(self, request, queryset):
        count = queryset.update(status = Post.Status.PUBLISHED)
        self.message_user(request, f'Изменено {count} записей')

    @admin.action(description='Снять с публикации выбранные записи')
    def set_draft(self, request, queryset):
        count = queryset.update(status = Post.Status.DRAFT)
        self.message_user(request, f'{count} записей снято с публикации', messages.WARNING)


@admin.register(Article)
class CommentAdmin(admin.ModelAdmin):
     fields = [("title", 'slug'), "body", "photo",]
     list_display = ['title', 'publish',]
     prepopulated_fields = {'slug': ('title',)}
     list_filter = ['publish']
     search_fields = ['title', 'body']
     ordering = ['publish']



class PhotoForm(ModelForm):
    class Meta:
        model = Photo
        fields = ['image']

class PhotoInline(admin.TabularInline):
    model = Photo
    form = PhotoForm
    extra = 1
    readonly_fields = ('thumbnail_preview',)

    def thumbnail_preview(self, instance):
        if instance.image:
            return format_html('<img src="{}" width="50" height="50"/>', instance.thumbnail.url)
        return "Нет фото"

    thumbnail_preview.short_description = 'Миниатюра'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    fields = [("title", 'slug'),('lat', 'lng'), "body"]
    list_display = ['title', 'publish', 'lat', 'lng']
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ['publish']
    search_fields = ['title', 'body']
    ordering = ['publish']
    inlines = [PhotoInline]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
     prepopulated_fields = {'slug': ('name',)}
     list_display = ('id', 'name')
     list_display_links = ('id', 'name')
     ordering = ('name',)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'tg_username','created_at','message','thumbnail','verified']
    ordering = ['verified', 'created_at']
    search_fields = ['name']

    def thumbnail(self, obj):
        if obj.photo:
            return format_html('<a href="{}" target="_blank">'
                               '<img src="{}" style="width: 50px; height: 50px; object-fit: cover;"/>'
                               '</a>', obj.photo.url, obj.photo.url)
        return "Нет фото"

    thumbnail.short_description = 'Фото'




