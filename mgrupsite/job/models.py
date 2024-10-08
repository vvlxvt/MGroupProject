from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone
from taggit.managers import TaggableManager
from .ru_taggit import RuTaggedItem

class PublichedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)

class Post(models.Model):

    class Status(models.TextChoices):
        DRAFT = 'DF','Draft'
        PUBLISHED = 'PB', 'Published'

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique_for_date='publish')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_posts')
    body = models.TextField()
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.DRAFT)
    tags = TaggableManager(through=RuTaggedItem)
    objects = models.Manager()
    published = PublichedManager()
    photo = models.ImageField(upload_to='photos/%Y/%m/%d', default=None, blank=True, null=True, verbose_name='photo')

    class Meta:
        ordering = ['-publish']
        indexes = [models.Index(fields=['-publish']),]

    def __str__(self):
        return self.title


    def get_absolute_url(self):
        # возвращает канонический URL-адрес объекта
        return reverse('job:post_detail',
                       args=[self.publish.year,
                            self.publish.month,
                            self.publish.day,
                            self.slug])

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=80)
    email = models.EmailField()
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['created']
        indexes = [models.Index(fields=['created']),]

    def __str__(self):
        return f'комментарий {self.name} на {self.post}'

class UploadFiles(models.Model):
    file = models.FileField(upload_to='uploads_model')


class Article (models.Model):

    class Status(models.TextChoices):
        DRAFT = 'DF','Draft'
        PUBLISHED = 'PB', 'Published'

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique_for_date='publish')
    body = models.TextField()
    publish = models.DateTimeField(default=timezone.now)
    objects = models.Manager()
    photo = models.ImageField(upload_to='photos/%Y/%m/%d', default=None, blank=True, null=True, verbose_name='photo')

    class Meta:
        ordering = ['-publish']
        indexes = [models.Index(fields=['-publish']),]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        # возвращает канонический URL-адрес объекта
        return reverse('job:article_detail',
                       args=[self.slug])

