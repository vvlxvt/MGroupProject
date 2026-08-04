from types import SimpleNamespace

from django.contrib.auth.models import User
from django.db import connection
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import get_resolver, reverse

from .models import (
    Article,
    Category,
    Photo,
    Post,
    Project,
    photo_upload_to,
    upload_to,
)
from .utils import chunk_list
from .views import page_not_found


class UploadPathTests(SimpleTestCase):
    def test_content_photo_path_contains_model_and_slug(self):
        instance = SimpleNamespace(
            __class__=SimpleNamespace(__name__="Article"),
            slug="surface-preparation",
        )

        path = upload_to(instance, "cover.jpg")

        self.assertTrue(path.endswith("/surface-preparation/cover.jpg"))

    def test_project_photo_path_contains_project_slug(self):
        instance = SimpleNamespace(
            project=SimpleNamespace(slug="factory-painting")
        )

        path = photo_upload_to(instance, "result.jpg")

        self.assertEqual(
            path,
            "photos/projects/factory-painting/result.jpg",
        )


class ChunkListTests(SimpleTestCase):
    def test_groups_items_into_requested_size(self):
        self.assertEqual(
            chunk_list([1, 2, 3, 4], 2),
            [(1, 2), (3, 4)],
        )

    def test_pads_last_group_with_none(self):
        self.assertEqual(
            chunk_list([1, 2, 3], 2),
            [(1, 2), (3, None)],
        )


class NotFoundPageTests(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get("/__missing-page__/")

    def test_handler_renders_custom_404_template(self):
        response = page_not_found(self.request, exception=Exception("Not found"))
        html = response.content.decode()

        self.assertEqual(response.status_code, 404)
        self.assertIn("<title>Ошибка 404 — Страница не найдена</title>", html)
        self.assertIn('<meta name="robots" content="noindex, nofollow">', html)
        self.assertNotIn('rel="canonical"', html)
        self.assertEqual(html.count('class="error-code'), 1)

    def test_custom_handler_is_registered(self):
        self.assertEqual(
            get_resolver().urlconf_module.handler404,
            "job.views.page_not_found",
        )


class HomeQueryTests(TestCase):
    def create_project(self, number):
        project = Project.objects.create(
            title=f"Проект {number}",
            slug=f"project-{number}",
        )
        Photo.objects.create(
            project=project,
            image=f"photos/projects/project-{number}/cover.jpg",
        )

    def home_query_count(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("job:home"))
        self.assertEqual(response.status_code, 200)
        return len(queries)

    def test_project_count_does_not_increase_home_queries(self):
        self.create_project(1)
        one_project_queries = self.home_query_count()

        for number in range(2, 6):
            self.create_project(number)

        many_project_queries = self.home_query_count()

        self.assertEqual(many_project_queries, one_project_queries)


class ArticleDetailQueryTests(TestCase):
    def create_article(self, number):
        return Article.objects.create(
            title=f"Статья {number}",
            slug=f"article-{number}",
            body=f"Текст статьи {number}",
        )

    def detail_query_count(self, article):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(
                reverse("job:article_detail", kwargs={"slug": article.slug})
            )
        self.assertEqual(response.status_code, 200)
        return len(queries)

    def test_sidebar_size_does_not_increase_detail_queries(self):
        detail_article = self.create_article(1)
        one_article_queries = self.detail_query_count(detail_article)

        for number in range(2, 6):
            self.create_article(number)

        many_article_queries = self.detail_query_count(detail_article)

        self.assertEqual(many_article_queries, one_article_queries)


class ServiceListQueryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        author = User.objects.create_user(username="author")
        category = Category.objects.create(
            name="Покраска",
            slug="painting",
        )
        for number in range(1, 3):
            Post.published.create(
                title=f"Услуга {number}",
                slug=f"service-{number}",
                author=author,
                body=f"Описание услуги {number}",
                status=Post.Status.PUBLISHED,
                cat=category,
            )

    def test_pagination_count_query_is_not_duplicated(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("job:post_list"))

        count_queries = [
            query["sql"]
            for query in queries
            if "COUNT(" in query["sql"].upper()
        ]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(count_queries), 1)
