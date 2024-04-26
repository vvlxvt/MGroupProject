from django.contrib import admin
from .forms import TagsForm
from .models import Post, Comment


@admin.register(Post)
class JobAdmin(admin.ModelAdmin):
    form = TagsForm
    fields = [("title", 'slug'),"author", "publish", 'tags']
    list_display = ['title', 'author', 'publish', 'status']
    list_filter = ['status', 'publish', 'author']
    search_fields = ['title', 'body']
    # prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author']
    date_hierarchy = 'publish'
    ordering = ['status', 'publish']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
     list_display = ['name','email','post','created','active']
     list_filter = ['active','created','updated']
     search_fields = ['name', 'email', 'body']




