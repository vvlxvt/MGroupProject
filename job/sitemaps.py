from django.contrib.sitemaps import GenericSitemap, Sitemap
from django.urls import reverse

from .models import Article, Post, Project

post_info = {
    "queryset": Post.objects.filter(status="PB"),
    "date_field": "updated",
}

project_info = {
    "queryset": Project.objects.all(),
    "date_field": "publish",
}

article_info = {
    "queryset": Article.objects.all(),
    "date_field": "publish",
}

post_sitemap = GenericSitemap(post_info, priority=0.9, changefreq="weekly")
project_sitemap = GenericSitemap(project_info, priority=0.8, changefreq="weekly")
article_sitemap = GenericSitemap(article_info, priority=0.6, changefreq="monthly")


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return [
            "job:home",
            "job:post_list",
            "job:projects",
            "job:article_list",
            "job:about",
            "job:contacts",
            "job:vacancies",
        ]

    def location(self, item):
        return reverse(item)


static_sitemap = StaticViewSitemap()
