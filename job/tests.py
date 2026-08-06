from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import get_resolver, reverse

from .context_processors import (
    MENU_CATEGORIES_CACHE_KEY,
    canonical_url,
    menu_context,
)
from .models import (
    Article,
    Category,
    Photo,
    Post,
    Project,
    UserProfile,
    UserQuestion,
    photo_upload_to,
    upload_to,
)
from .utils import chunk_list
from .utils import ExternalServiceUnavailable
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


@override_settings(ALLOWED_HOSTS=["xn--c1arkads.xn--p1ai"])
class SitemapTests(TestCase):
    def test_sitemap_uses_requested_production_domain(self):
        response = self.client.get(
            reverse("sitemap"),
            secure=True,
            HTTP_HOST="xn--c1arkads.xn--p1ai",
        )
        xml = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertIn(
            "https://xn--c1arkads.xn--p1ai/",
            xml,
        )
        self.assertNotIn("example.com", xml)
        self.assertNotIn("mgroup-vvlxvt.amvera.io", xml)

    def test_robots_points_to_sitemap_on_current_domain(self):
        response = self.client.get(
            "/robots.txt",
            secure=True,
            HTTP_HOST="xn--c1arkads.xn--p1ai",
        )

        self.assertContains(
            response,
            "Sitemap: https://xn--c1arkads.xn--p1ai/sitemap.xml",
        )


@override_settings(
    ALLOWED_HOSTS=["testserver"],
    CANONICAL_BASE_URL="https://example.test",
)
class CanonicalUrlTests(TestCase):
    def test_page_has_absolute_canonical_url(self):
        response = self.client.get(reverse("job:home"))

        self.assertContains(
            response,
            '<link rel="canonical" href="https://example.test/">',
        )

    def test_filter_parameters_are_removed_from_canonical_url(self):
        request = RequestFactory().get(
            "/services/",
            {"category": "painting", "query": "metal"},
        )

        self.assertEqual(
            canonical_url(request)["canonical_url"],
            "https://example.test/services/",
        )

    def test_pagination_page_is_preserved_in_canonical_url(self):
        request = RequestFactory().get("/services/", {"page": "2"})

        self.assertEqual(
            canonical_url(request)["canonical_url"],
            "https://example.test/services/?page=2",
        )

    def test_404_page_has_no_canonical_url(self):
        response = self.client.get("/__missing-canonical-page__/")

        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, 'rel="canonical"', status_code=404)


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
        cache.delete(MENU_CATEGORIES_CACHE_KEY)
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
        cache.delete(MENU_CATEGORIES_CACHE_KEY)
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


class ProjectLocationsJsonTests(TestCase):
    def test_project_titles_are_safely_embedded_as_json(self):
        title = 'Проект "Север" </script><script>alert(1)</script>'
        Project.objects.create(
            title=title,
            slug="safe-json-project",
            lat=56.02,
            lng=93.03,
        )

        response = self.client.get(reverse("job:projects"))
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn('id="project-locations"', html)
        self.assertIn(r"\u003C/script\u003E", html)
        self.assertNotIn("</script><script>alert(1)</script>", html)
        self.assertEqual(response.context["locations"][0]["title"], title)


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


class ContentSlugUniquenessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(username="slug-author")
        cls.category = Category.objects.create(
            name="Защита",
            slug="protection",
        )

    def assert_duplicate_slug_is_rejected(self, create_object):
        create_object()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                create_object()

    def test_post_slug_is_globally_unique(self):
        self.assert_duplicate_slug_is_rejected(
            lambda: Post.objects.create(
                title="Услуга",
                slug="shared-service",
                author=self.author,
                body="Описание",
                cat=self.category,
            )
        )

    def test_article_slug_is_globally_unique(self):
        self.assert_duplicate_slug_is_rejected(
            lambda: Article.objects.create(
                title="Статья",
                slug="shared-article",
                body="Текст",
            )
        )

    def test_project_slug_is_globally_unique(self):
        self.assert_duplicate_slug_is_rejected(
            lambda: Project.objects.create(
                title="Проект",
                slug="shared-project",
                body="Описание",
            )
        )


class SubmitQuestionDeliveryTests(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            telegram_id=123456,
            username="customer",
        )

    def submit_question(self):
        with patch("job.views.verify_recaptcha"):
            return self.client.post(
                reverse("job:submit_question"),
                {
                    "telegram_id": self.user.telegram_id,
                    "question_text": "Нужна консультация по проекту",
                    "recaptcha_token": "test-token",
                },
            )

    def test_question_is_queued_without_synchronous_telegram_request(self):
        with patch("job.utils.requests.post") as telegram_request:
            response = self.submit_question()
        question = UserQuestion.objects.get()

        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.json()["success"])
        telegram_request.assert_not_called()
        self.assertEqual(
            question.telegram_status,
            UserQuestion.DeliveryStatus.PENDING,
        )

    def test_unavailable_recaptcha_returns_service_unavailable(self):
        with patch(
            "job.views.verify_recaptcha",
            side_effect=ExternalServiceUnavailable,
        ):
            response = self.client.post(
                reverse("job:submit_question"),
                {
                    "telegram_id": self.user.telegram_id,
                    "question_text": "Нужна консультация по проекту",
                    "recaptcha_token": "test-token",
                },
            )

        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()["success"])
        self.assertFalse(UserQuestion.objects.exists())


class ProcessQuestionNotificationsTests(TestCase):
    def setUp(self):
        user = UserProfile.objects.create(
            telegram_id=654321,
            username="queued-customer",
        )
        self.question = UserQuestion.objects.create(
            user=user,
            question_text="Вопрос для фоновой отправки",
        )

    def test_worker_marks_successful_delivery_as_sent(self):
        with patch(
            "job.management.commands.process_question_notifications.send_telegram_message",
            return_value=True,
        ):
            call_command("process_question_notifications")

        self.question.refresh_from_db()
        self.assertEqual(
            self.question.telegram_status,
            UserQuestion.DeliveryStatus.SENT,
        )

    def test_worker_marks_failed_delivery_as_failed(self):
        with patch(
            "job.management.commands.process_question_notifications.send_telegram_message",
            return_value=False,
        ):
            call_command("process_question_notifications")

        self.question.refresh_from_db()
        self.assertEqual(
            self.question.telegram_status,
            UserQuestion.DeliveryStatus.FAILED,
        )


class MenuContextCacheTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Промышленная покраска",
            slug="industrial-painting",
            number=1,
        )
        cache.clear()

    def test_repeated_menu_context_does_not_query_database(self):
        with CaptureQueriesContext(connection) as first_queries:
            first_context = menu_context(None)
        with CaptureQueriesContext(connection) as cached_queries:
            second_context = menu_context(None)

        self.assertEqual(len(first_queries), 1)
        self.assertEqual(len(cached_queries), 0)
        self.assertEqual(second_context, first_context)

    def test_category_update_invalidates_cached_menu(self):
        menu_context(None)
        self.category.name = "Обновлённая категория"

        with self.captureOnCommitCallbacks(execute=True):
            self.category.save(update_fields=["name"])

        context = menu_context(None)
        submenu = context["menu"]["services"]["submenus"]
        self.assertEqual(submenu[0]["title"], "Обновлённая категория")

    def test_category_delete_invalidates_cached_menu(self):
        menu_context(None)

        with self.captureOnCommitCallbacks(execute=True):
            self.category.delete()

        context = menu_context(None)
        self.assertEqual(context["menu"]["services"]["submenus"], [])
