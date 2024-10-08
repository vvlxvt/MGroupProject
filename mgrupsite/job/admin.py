from django.contrib import admin, messages
from .forms import TagsForm
from .models import Post, Comment, Article

@admin.register(Post)
class JobAdmin(admin.ModelAdmin):
    form = TagsForm
    fields = [("title", 'slug'),"author", "body", 'tags', "photo",]
    list_display = ['title', 'author', 'publish', 'status',]
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ['status', 'publish', 'author']
    search_fields = ['title', 'body']
    raw_id_fields = ['author']
    date_hierarchy = 'publish'
    ordering = ['status', 'publish']
    actions = ['set_published', 'set_draft']

    @admin.action(description='Опубликовать выбранные записи')
    # добавляем действие к выбранным записям в админку
    def set_published(self, request, queryset):
        count = queryset.update(status = Post.Status.PUBLISHED)
        self.message_user(request, f'Изменено {count} записей')

    @admin.action(description='Снять с публикации выбранные записи')
    def set_draft(self, request, queryset):
        count = queryset.update(status = Post.Status.DRAFT)
        self.message_user(request, f'{count} записей снято с публикации', messages.WARNING)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
     list_display = ['name','email','post','created','active']
     list_filter = ['active','created','updated']
     search_fields = ['name', 'email', 'body']


@admin.register(Article)
class CommentAdmin(admin.ModelAdmin):
     fields = [("title", 'slug'), "body", "photo",]
     list_display = ['title', 'publish',]
     prepopulated_fields = {'slug': ('title',)}
     list_filter = ['publish']
     search_fields = ['title', 'body']
     ordering = ['publish']



