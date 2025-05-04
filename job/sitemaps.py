from django.contrib.sitemaps import Sitemap

from django.contrib.sitemaps import GenericSitemap
from .models import Project, Article, Post

post_info = {
    'queryset': Post.objects.all(),
    'date_field': 'updated',
}

project_info = {
    'queryset': Project.objects.all(),
    'date_field': 'publish',
}

article_info = {
    'queryset': Article.objects.all(),
    'date_field': 'publish',
}

post_sitemap = GenericSitemap(post_info, priority=0.9, changefreq='weekly')
project_sitemap = GenericSitemap(project_info, priority=0.8, changefreq='weekly')
article_sitemap = GenericSitemap(article_info, priority=0.6, changefreq='monthly')
