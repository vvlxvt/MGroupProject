from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, EmailValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from taggit.managers import TaggableManager
from .ru_taggit import RuTaggedItem
from ckeditor.fields import RichTextField
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill


class PublichedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)

def upload_to(instance, filename):
    class_name = instance.__class__.__name__.lower()
    return f'photos/{class_name}/{instance.slug}/{filename}'

class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DF','Draft'
        PUBLISHED = 'PB', 'Published'

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique_for_date='publish')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_posts')
    body =  RichTextField()
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.DRAFT)
    number = models.IntegerField(blank=True, null=True)
    tags = TaggableManager(through=RuTaggedItem)
    objects = models.Manager()
    published = PublichedManager()
    cat = models.ForeignKey('Category', on_delete=models.DO_NOTHING, related_name='posts',
    verbose_name="Категория") # чтобы добавить поле надо сделать сначала с null=True, потом без него
    photo = models.ImageField(upload_to=upload_to, default=None, blank=True, null=True,
                              verbose_name='Фото')
    articles = models.ManyToManyField('Article', through='PostArticle', related_name='posts')

    class Meta:
        ordering = ['number']
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

class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    slug = models.CharField(max_length=100, db_index=True, unique=True)
    number = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.name


class UploadFiles(models.Model):
    file = models.FileField(upload_to='uploads_model')


class Article (models.Model):
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique_for_date='publish')
    body = RichTextField()
    publish = models.DateTimeField(default=timezone.now)
    objects = models.Manager()
    photo = models.ImageField(upload_to=upload_to, max_length=255, default=None, blank=True, null=True)

    class Meta:
        ordering = ['title']
        indexes = [models.Index(fields=['-publish']),]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        # возвращает канонический URL-адрес объекта
        return reverse('job:article_detail',
                       args=[self.slug])

class PostArticle(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    number = models.IntegerField(blank=True)

class Project(models.Model):
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique_for_date='publish')
    body = models.TextField()
    lat = models.FloatField(null=True,blank=True,validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)])
    lng = models.FloatField(null=True,blank=True,validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)])
    publish = models.DateTimeField(default=timezone.now)
    objects = models.Manager()

    class Meta:
        ordering = ['-publish']
        indexes = [models.Index(fields=['-publish']), ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        # возвращает канонический URL-адрес объекта
        return reverse('job:project_detail', args=[self.slug])

def photo_upload_to(instance, filename):
    # Путь для загрузки файлов, используя slug проекта
    project_slug = instance.project.slug
    return f'photos/projects/{project_slug}/{filename}'

class Photo(models.Model):
    project = models.ForeignKey(Project, related_name='photos', on_delete=models.CASCADE)  # Связь с моделью Project
    image = models.ImageField(upload_to=photo_upload_to)
    thumbnail = ImageSpecField(source='image',
                               processors=[ResizeToFill(50, 50)],
                               format='JPEG',options={'quality': 60})

    def __str__(self):
        return f"Фото для {self.project.title}"

def photo_upload(instance, filename):
    class_name = instance.__class__.__name__.lower()

    return f'photos/{class_name}/{instance.tg_username}/{filename}'

class Contact(models.Model):
    name = models.CharField(max_length=100)
    tg_username = models.CharField(unique=True,max_length=100)
    tg_id = models.BigIntegerField(unique=True, null=True, blank=True)
    # company = models.CharField(unique=True,max_length=100, blank=True)
    # city = models.CharField(unique=True,max_length=100, blank=True)
    email = models.EmailField(blank=True, null=True)
    message = models.TextField()
    photo = models.ImageField(upload_to=photo_upload, blank=True, null=True)  # Добавляем поле для фотографий
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.tg_username

