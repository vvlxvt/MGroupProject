import json
import re
import time
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import call, patch

import requests
from botocore.exceptions import ClientError
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management import call_command, CommandError
from django.db import IntegrityError, connection, transaction
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import get_resolver, reverse
from django.utils import timezone
from django_tiptap_editor.widgets.admin_tiptap import AdminTipTapWidget

from .admin import CommentAdmin, JobAdmin
from .context_processors import (
    MENU_CATEGORIES_CACHE_KEY,
    canonical_url,
    menu_context,
)
from .models import (
    Article,
    ApplicantProfile,
    Category,
    Photo,
    Post,
    Project,
    UserQuestion,
    photo_upload_to,
    upload_to,
)
from .utils import chunk_list
from .utils import ExternalServiceUnavailable
from .views import page_not_found
from mgrupsite.settings.validators import is_weak_secret_key


class ProductionSecretKeyValidationTests(SimpleTestCase):
    def test_rejects_short_or_template_secret_keys(self):
        self.assertTrue(is_weak_secret_key("short-secret"))
        self.assertTrue(is_weak_secret_key("django-insecure-" + "a" * 60))
        self.assertTrue(is_weak_secret_key("a" * 80))

    def test_accepts_long_random_secret_key(self):
        self.assertFalse(
            is_weak_secret_key(
                "jK8mQ2wZ5rT9yP4nL7vX3cB6sD1fG0hJ8kM2qW5eR9tY4uI7oP3aS6dF"
            )
        )


class ContentSecurityPolicyTests(TestCase):
    @override_settings(CSP_REPORT_ONLY_ENABLED=True)
    def test_html_response_has_report_only_policy(self):
        response = self.client.get(reverse("job:privacy"))

        policy = response["Content-Security-Policy-Report-Only"]
        self.assertIn("default-src 'self'", policy)
        self.assertIn("object-src 'none'", policy)
        self.assertIn("https://www.google.com", policy)
        self.assertIn("wss://mc.yandex.ru", policy)
        self.assertNotIn("Content-Security-Policy", response)

    @override_settings(CSP_REPORT_ONLY_ENABLED=True)
    def test_policy_nonce_matches_rendered_script_nonce(self):
        response = self.client.get(reverse("job:privacy"))

        policy = response["Content-Security-Policy-Report-Only"]
        nonce = re.search(r"'nonce-([^']+)'", policy).group(1)
        self.assertContains(response, f'nonce="{nonce}"')
        script_directive = policy.split("script-src", 1)[1].split(";", 1)[0]
        self.assertNotIn("'unsafe-inline'", script_directive)
        self.assertIn("'strict-dynamic'", script_directive)

    @override_settings(CSP_REPORT_ONLY_ENABLED=True)
    def test_each_response_uses_a_different_nonce(self):
        first = self.client.get(reverse("job:privacy"))
        second = self.client.get(reverse("job:privacy"))

        first_policy = first["Content-Security-Policy-Report-Only"]
        second_policy = second["Content-Security-Policy-Report-Only"]
        first_nonce = re.search(r"'nonce-([^']+)'", first_policy).group(1)
        second_nonce = re.search(r"'nonce-([^']+)'", second_policy).group(1)
        self.assertNotEqual(first_nonce, second_nonce)

    @override_settings(CSP_REPORT_ONLY_ENABLED=True)
    def test_plain_text_response_does_not_have_policy(self):
        response = self.client.get("/robots.txt")

        self.assertNotIn("Content-Security-Policy-Report-Only", response)


class MediaUrlTemplateTests(TestCase):
    @override_settings(MEDIA_URL="https://media.example.test/")
    def test_favicon_urls_are_absolute_on_nested_pages(self):
        response = self.client.get(reverse("job:post_list"))

        self.assertContains(
            response,
            'href="https://media.example.test/photos/Logo/favicon/m_logo_64.png"',
        )
        self.assertContains(
            response,
            'href="https://media.example.test/photos/Logo/favicon/m_logo_32.png"',
        )

    def test_project_map_uses_current_advanced_marker_api(self):
        response = self.client.get(reverse("job:projects"))

        self.assertContains(response, "glyphText: `${id}`")
        self.assertContains(response, 'marker.addEventListener("gmp-click"')
        self.assertNotContains(response, "glyph: `${id}`")
        self.assertNotContains(response, "pin.element")

    @override_settings(CSP_REPORT_ONLY_ENABLED=False)
    def test_report_only_policy_can_be_disabled(self):
        response = self.client.get(reverse("job:privacy"))

        self.assertNotIn("Content-Security-Policy-Report-Only", response)


class RichTextEditorTests(SimpleTestCase):
    def test_post_body_uses_tiptap_admin_widget(self):
        model_admin = JobAdmin(Post, admin.site)
        form_field = model_admin.formfield_for_dbfield(
            Post._meta.get_field("body"), request=None
        )

        self.assertIsInstance(form_field.widget, AdminTipTapWidget)

    def test_article_body_uses_tiptap_admin_widget(self):
        model_admin = CommentAdmin(Article, admin.site)
        form_field = model_admin.formfield_for_dbfield(
            Article._meta.get_field("body"), request=None
        )

        self.assertIsInstance(form_field.widget, AdminTipTapWidget)


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


class PageHeadingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        author = User.objects.create_user(username="heading-author")
        category = Category.objects.create(
            name="Промышленная покраска",
            slug="industrial-painting",
        )
        cls.posts = [
            Post.published.create(
                title=f"Услуга {number}",
                slug=f"heading-service-{number}",
                author=author,
                body="Описание услуги",
                status=Post.Status.PUBLISHED,
                cat=category,
            )
            for number in range(1, 3)
        ]
        cls.article = Article.objects.create(
            title="Статья о подготовке поверхности",
            slug="heading-article",
            body="Текст статьи",
        )
        cls.project = Project.objects.create(
            title="Покраска промышленного объекта",
            slug="heading-project",
            body="Описание проекта",
        )

    def test_indexable_pages_have_one_h1(self):
        urls = [
            reverse("job:home"),
            reverse("job:post_list"),
            self.posts[0].get_absolute_url(),
            reverse("job:projects"),
            self.project.get_absolute_url(),
            reverse("job:article_list"),
            self.article.get_absolute_url(),
            reverse("job:about"),
            reverse("job:contacts"),
            reverse("job:vacancies"),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content.decode().lower().count("<h1"), 1)

    def test_indexable_pages_have_description_and_open_graph_metadata(self):
        urls = [
            reverse("job:home"),
            reverse("job:post_list"),
            self.posts[0].get_absolute_url(),
            reverse("job:projects"),
            self.project.get_absolute_url(),
            reverse("job:article_list"),
            self.article.get_absolute_url(),
            reverse("job:about"),
            reverse("job:contacts"),
            reverse("job:vacancies"),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                html = response.content.decode()
                description = re.search(
                    r'<meta name="description" content="([^"]+)">',
                    html,
                )

                self.assertEqual(response.status_code, 200)
                self.assertIsNotNone(description)
                self.assertNotIn("{{", description.group(1))
                for property_name in (
                    "og:title",
                    "og:description",
                    "og:image",
                    "og:url",
                ):
                    self.assertEqual(
                        html.count(f'property="{property_name}"'),
                        1,
                    )

                og_image = re.search(
                    r'<meta property="og:image" content="([^"]+)">',
                    html,
                )
                self.assertIsNotNone(og_image)
                self.assertTrue(og_image.group(1).startswith("http"))

    def test_dynamic_seo_titles_and_descriptions_have_useful_length(self):
        urls = [
            reverse("job:home"),
            reverse("job:article_list"),
            reverse("job:vacancies"),
            self.posts[0].get_absolute_url(),
            self.article.get_absolute_url(),
            self.project.get_absolute_url(),
        ]

        for url in urls:
            with self.subTest(url=url):
                html = self.client.get(url).content.decode()
                title = re.search(r"<title>([^<]+)</title>", html).group(1)
                self.assertGreaterEqual(len(title), 30)
                self.assertLessEqual(len(title), 60)

        for url in (
            self.posts[0].get_absolute_url(),
            self.article.get_absolute_url(),
            self.project.get_absolute_url(),
        ):
            with self.subTest(description_url=url):
                html = self.client.get(url).content.decode()
                description = re.search(
                    r'<meta name="description" content="([^"]+)">', html
                ).group(1)
                self.assertGreaterEqual(len(description), 100)
                self.assertLessEqual(len(description), 160)

    def test_pages_expose_expected_json_ld_entities(self):
        cases = {
            reverse("job:contacts"): {"LocalBusiness", "BreadcrumbList"},
            self.posts[0].get_absolute_url(): {
                "LocalBusiness",
                "BreadcrumbList",
                "Service",
            },
            self.article.get_absolute_url(): {
                "LocalBusiness",
                "BreadcrumbList",
                "Article",
            },
            self.project.get_absolute_url(): {"LocalBusiness", "BreadcrumbList"},
        }

        for url, expected_types in cases.items():
            with self.subTest(url=url):
                html = self.client.get(url).content.decode()
                payloads = re.findall(
                    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
                    html,
                    re.DOTALL,
                )
                schema_types = {json.loads(payload)["@type"] for payload in payloads}
                self.assertTrue(expected_types.issubset(schema_types))

    def test_html_responses_are_gzip_compressed_when_supported(self):
        response = self.client.get(
            reverse("job:home"), HTTP_ACCEPT_ENCODING="gzip"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Content-Encoding"), "gzip")
        self.assertIn("Accept-Encoding", response.headers.get("Vary", ""))

    def test_services_and_projects_link_to_each_other(self):
        self.project.services.add(self.posts[0])

        service_response = self.client.get(self.posts[0].get_absolute_url())
        project_response = self.client.get(self.project.get_absolute_url())

        self.assertContains(
            service_response,
            f'href="{self.project.get_absolute_url()}"',
        )
        self.assertContains(service_response, "Проекты с этой услугой")
        self.assertContains(
            project_response,
            f'href="{self.posts[0].get_absolute_url()}"',
        )
        self.assertContains(project_response, "Выполненные услуги")

    def test_detail_pages_keep_their_menu_section_active(self):
        cases = {
            self.posts[0].get_absolute_url(): ("services", "Услуги"),
            self.article.get_absolute_url(): ("articles", "Статьи"),
            self.project.get_absolute_url(): ("projects", "Проекты"),
            reverse("job:applicant"): ("calculator", "Вакансии"),
        }

        for url, (menu_key, label) in cases.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                html = response.content.decode()

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["active_menu_key"], menu_key)
                self.assertEqual(html.count('aria-current="page"'), 1)
                self.assertRegex(
                    html,
                    rf'<a class="nav-link[^"]*active[^"]*"[^>]*'
                    rf'aria-current="page"[^>]*>\s*{label}\s*</a>',
                )

    def test_contacts_controls_have_accessible_names_and_heading_order(self):
        html = self.client.get(reverse("job:contacts")).content.decode()

        self.assertRegex(
            html,
            r'<button class="btn" type="submit" aria-label="Найти на сайте">',
        )
        for control_id in (
            "site-search",
            "contact-email",
            "contact-question",
            "contact-photo",
        ):
            with self.subTest(control_id=control_id):
                self.assertIn(f'for="{control_id}"', html)
                self.assertIn(f'id="{control_id}"', html)

        self.assertIn('title="Карта проезда к офису Маляр Групп"', html)
        self.assertNotIn("contacts-details", html)
        self.assertNotIn('<h5 class="footer-title">', html)
        self.assertEqual(html.count('<h2 class="footer-title h5">'), 4)

    def test_home_headings_do_not_skip_section_levels(self):
        html = self.client.get(reverse("job:home")).content.decode()

        self.assertIn(
            '<h2 class="visually-hidden">Опыт и возможности компании</h2>',
            html,
        )
        self.assertNotIn('<h6 class="card-title project-card__title">', html)
        self.assertIn('<h3 class="h6 card-title project-card__title">', html)


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
        cache.clear()

    def test_contact_page_does_not_expose_telegram_login_or_profile_fields(self):
        response = self.client.get(reverse("job:contacts"))

        self.assertNotContains(response, "telegram-widget.js")
        self.assertNotContains(response, 'name="telegram_id"')
        self.assertNotContains(response, 'name="username"')
        self.assertNotContains(response, 'name="city"')
        self.assertContains(response, 'name="contact_email"')

    def test_legacy_telegram_callback_is_not_available(self):
        response = self.client.get("/callback/")

        self.assertEqual(response.status_code, 404)

    def submit_question(self):
        with patch("job.views.validate_form_token", return_value=True), patch(
            "job.views.verify_recaptcha"
        ):
            return self.client.post(
                reverse("job:submit_question"),
                {
                    "contact_email": "customer@example.com",
                    "question_text": "Нужна консультация по проекту",
                    "recaptcha_token": "test-token",
                    "personal_data_consent": "1",
                },
            )

    def test_question_is_queued_without_synchronous_telegram_request(self):
        with patch("job.utils.requests.post") as telegram_request:
            response = self.submit_question()
        question = UserQuestion.objects.get()

        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.json()["success"])
        self.assertEqual(question.contact_email, "customer@example.com")
        self.assertIsNone(question.user)
        telegram_request.assert_not_called()
        self.assertEqual(
            question.telegram_status,
            UserQuestion.DeliveryStatus.PENDING,
        )

    def test_unavailable_recaptcha_returns_service_unavailable(self):
        with patch(
            "job.views.verify_recaptcha",
            side_effect=ExternalServiceUnavailable,
        ), patch("job.views.validate_form_token", return_value=True):
            response = self.client.post(
                reverse("job:submit_question"),
                {
                    "contact_email": "customer@example.com",
                    "question_text": "Нужна консультация по проекту",
                    "recaptcha_token": "test-token",
                },
            )

        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()["success"])
        self.assertFalse(UserQuestion.objects.exists())

    def test_honeypot_submission_is_accepted_without_saving_or_external_calls(self):
        with patch("job.views.verify_recaptcha") as recaptcha:
            response = self.client.post(
                reverse("job:submit_question"),
                {"website": "https://spam.example", "question_text": "spam"},
            )

        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.json()["success"])
        self.assertFalse(UserQuestion.objects.exists())
        recaptcha.assert_not_called()

    def test_invalid_form_token_is_rejected(self):
        response = self.client.post(
            reverse("job:submit_question"),
            {
                "form_token": "invalid",
                "contact_email": "customer@example.com",
                "question_text": "Нужна консультация по проекту",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(UserQuestion.objects.exists())

    def test_question_consent_is_required(self):
        with patch("job.views.validate_form_token", return_value=True), patch(
            "job.views.verify_recaptcha"
        ):
            response = self.client.post(
                reverse("job:submit_question"),
                {
                    "contact_email": "customer@example.com",
                    "question_text": "Нужна консультация по проекту",
                    "recaptcha_token": "test-token",
                },
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("personal_data_consent", response.json()["errors"])
        self.assertFalse(UserQuestion.objects.exists())

    def test_repeated_email_is_rate_limited(self):
        responses = []
        with patch("job.views.validate_form_token", return_value=True), patch(
            "job.views.verify_recaptcha"
        ):
            for number in range(4):
                responses.append(
                    self.client.post(
                        reverse("job:submit_question"),
                        {
                            "contact_email": "repeat@example.com",
                            "question_text": f"Вопрос номер {number} для консультации",
                            "recaptcha_token": "test-token",
                            "personal_data_consent": "1",
                        },
                    )
                )

        self.assertEqual([response.status_code for response in responses], [202, 202, 202, 429])
        self.assertEqual(UserQuestion.objects.count(), 3)
        self.assertEqual(responses[-1].headers["Retry-After"], "3600")


class ApplicantFeedbackTests(TestCase):
    def setUp(self):
        cache.clear()

    def submit(self, **overrides):
        data = {
            "name": "Иван",
            "position": "Маляр",
            "experience": "Пять лет промышленной окраски",
            "telephone_number": "+7 999 123-45-67",
            "recaptcha_token": "test-token",
            "personal_data_consent": "on",
        }
        data.update(overrides)
        return self.client.post(reverse("job:applicant"), data)

    def test_selected_vacancy_prefills_position(self):
        response = self.client.get(
            reverse("job:applicant"),
            {"vacancy": "anticorrosion-painter"},
        )

        self.assertContains(response, 'value="Маляр антикоррозийных работ"')

    def test_unknown_vacancy_does_not_prefill_arbitrary_text(self):
        response = self.client.get(
            reverse("job:applicant"),
            {"vacancy": "<script>alert(1)</script>"},
        )

        self.assertEqual(response.context["form"].initial["position"], "")

    def test_minimal_applicant_data_is_saved(self):
        with patch("job.views.validate_form_token", return_value=True), patch(
            "job.views.verify_recaptcha"
        ):
            response = self.submit()

        applicant = ApplicantProfile.objects.get()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ваша анкета отправлена")
        self.assertEqual(applicant.name, "Иван")
        self.assertEqual(applicant.surname, "")
        self.assertEqual(applicant.experience, "Пять лет промышленной окраски")

    def test_phone_or_email_is_required(self):
        with patch("job.views.validate_form_token", return_value=True), patch(
            "job.views.verify_recaptcha"
        ):
            response = self.submit(telephone_number="", email="")

        self.assertContains(response, "Укажите телефон или email")
        self.assertFalse(ApplicantProfile.objects.exists())

    def test_applicant_consent_is_required(self):
        with patch("job.views.validate_form_token", return_value=True), patch(
            "job.views.verify_recaptcha"
        ):
            response = self.submit(personal_data_consent="")

        self.assertContains(response, "Подтвердите согласие")
        self.assertFalse(ApplicantProfile.objects.exists())

    def test_honeypot_does_not_save_or_call_recaptcha(self):
        with patch("job.views.verify_recaptcha") as recaptcha:
            response = self.submit(website="https://spam.example")

        self.assertContains(response, "Ваша анкета отправлена")
        self.assertFalse(ApplicantProfile.objects.exists())
        recaptcha.assert_not_called()

    def test_contact_is_rate_limited(self):
        with patch("job.views.validate_form_token", return_value=True), patch(
            "job.views.verify_recaptcha"
        ):
            responses = [self.submit() for _ in range(3)]

        self.assertEqual(ApplicantProfile.objects.count(), 2)
        self.assertContains(responses[-1], "Слишком много откликов")


class ProcessQuestionNotificationsTests(TestCase):
    def setUp(self):
        self.question = UserQuestion.objects.create(
            contact_email="queued@example.com",
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


class ProcessFeedbackNotificationsTests(TestCase):
    def test_worker_delivers_question_and_applicant(self):
        question = UserQuestion.objects.create(
            contact_email="customer@example.com",
            question_text="Нужна консультация",
        )
        applicant = ApplicantProfile.objects.create(
            name="Иван",
            position="Маляр",
            experience="Пять лет опыта",
            telephone_number="+7 999 123-45-67",
        )

        with patch(
            "job.management.commands.process_feedback_notifications.send_telegram_message",
            return_value=True,
        ), patch(
            "job.management.commands.process_feedback_notifications.send_telegram_applicant",
            return_value=True,
        ):
            call_command("process_feedback_notifications")

        question.refresh_from_db()
        applicant.refresh_from_db()
        self.assertEqual(question.telegram_status, UserQuestion.DeliveryStatus.SENT)
        self.assertEqual(applicant.telegram_status, UserQuestion.DeliveryStatus.SENT)

    def test_continuous_worker_can_run_single_iteration(self):
        with patch(
            "job.management.commands.run_feedback_worker.call_command"
        ) as process_feedback:
            call_command("run_feedback_worker", once=True, interval=10, limit=7)

        process_feedback.assert_called_once_with(
            "process_feedback_notifications",
            limit=7,
            retry_failed=True,
        )

    @override_settings(
        PRODUCTION_BACKUP_ENABLED=True,
        PRODUCTION_BACKUP_INTERVAL_SECONDS=86400,
        PRODUCTION_BACKUP_RETRY_SECONDS=3600,
    )
    def test_worker_runs_due_production_backup(self):
        cache.delete("production-backup:last-success")
        with patch(
            "job.management.commands.run_feedback_worker.call_command"
        ) as worker_command:
            call_command("run_feedback_worker", once=True, interval=10, limit=7)

        self.assertEqual(
            worker_command.call_args_list,
            [
                call(
                    "process_feedback_notifications",
                    limit=7,
                    retry_failed=True,
                ),
                call("backup_production"),
            ],
        )
        self.assertIsNotNone(cache.get("production-backup:last-success"))

    @override_settings(
        PRODUCTION_BACKUP_ENABLED=True,
        PRODUCTION_BACKUP_INTERVAL_SECONDS=86400,
        PRODUCTION_BACKUP_RETRY_SECONDS=3600,
    )
    def test_worker_skips_recent_production_backup(self):
        cache.set("production-backup:last-success", time.time(), timeout=None)
        with patch(
            "job.management.commands.run_feedback_worker.call_command"
        ) as worker_command:
            call_command("run_feedback_worker", once=True, interval=10, limit=7)

        worker_command.assert_called_once_with(
            "process_feedback_notifications",
            limit=7,
            retry_failed=True,
        )

    @override_settings(
        PRODUCTION_BACKUP_ENABLED=True,
        PRODUCTION_BACKUP_INTERVAL_SECONDS=86400,
        PRODUCTION_BACKUP_RETRY_SECONDS=3600,
    )
    def test_backup_failure_does_not_stop_worker_or_mark_success(self):
        cache.delete("production-backup:last-success")

        def command_side_effect(command_name, **options):
            if command_name == "backup_production":
                raise RuntimeError("backup unavailable")

        with patch(
            "job.management.commands.run_feedback_worker.call_command",
            side_effect=command_side_effect,
        ):
            call_command("run_feedback_worker", once=True, interval=10, limit=7)

        self.assertIsNone(cache.get("production-backup:last-success"))

    @patch("job.utils.requests.post")
    def test_applicant_notification_mentions_selected_business_trips(self, telegram_request):
        from job.utils import send_telegram_applicant

        telegram_request.return_value.raise_for_status.return_value = None
        applicant = ApplicantProfile.objects.create(
            name="Иван",
            position="Маляр",
            telephone_number="+7 999 123-45-67",
            ready_for_business_trip=True,
        )

        self.assertTrue(send_telegram_applicant(applicant))
        self.assertIn("Готов к командировкам", telegram_request.call_args.kwargs["data"]["text"])

    @patch("job.utils.requests.post")
    def test_applicant_notification_omits_unselected_business_trips(self, telegram_request):
        from job.utils import send_telegram_applicant

        telegram_request.return_value.raise_for_status.return_value = None
        applicant = ApplicantProfile.objects.create(
            name="Иван",
            position="Маляр",
            telephone_number="+7 999 123-45-67",
            ready_for_business_trip=False,
        )

        self.assertTrue(send_telegram_applicant(applicant))
        self.assertNotIn("командировкам", telegram_request.call_args.kwargs["data"]["text"])


class TelegramFailureLoggingTests(SimpleTestCase):
    def test_logs_exception_type_and_http_status_without_sensitive_data(self):
        from job.utils import _log_telegram_delivery_failure

        error = requests.HTTPError(response=SimpleNamespace(status_code=401))

        with self.assertLogs("job.utils", level="ERROR") as captured:
            _log_telegram_delivery_failure("question", error)

        log_entry = " ".join(captured.output)
        self.assertIn("error_type=HTTPError", log_entry)
        self.assertIn("status_code=401", log_entry)
        self.assertNotIn("bot_token", log_entry)
        self.assertNotIn("chat_id", log_entry)

    def test_logs_na_when_no_http_response_exists(self):
        from job.utils import _log_telegram_delivery_failure

        with self.assertLogs("job.utils", level="ERROR") as captured:
            _log_telegram_delivery_failure("applicant", TimeoutError())

        self.assertIn("status_code=n/a", " ".join(captured.output))


class TelegramMissingAttachmentTests(TestCase):
    @patch("job.utils.requests.post")
    def test_missing_attachment_falls_back_to_text_message(self, telegram_request):
        from job.utils import send_telegram_message

        telegram_request.return_value.raise_for_status.return_value = None
        question = UserQuestion(
            contact_email="customer@example.com",
            question_text="Нужна консультация",
            attached_photo="questions/missing.jpg",
        )

        with patch.object(
            question.attached_photo,
            "open",
            side_effect=FileNotFoundError,
        ), self.assertLogs("job.utils", level="WARNING"):
            delivered = send_telegram_message(question)

        self.assertTrue(delivered)
        self.assertTrue(telegram_request.call_args.args[0].endswith("/sendMessage"))
        self.assertNotIn("files", telegram_request.call_args.kwargs)


class FeedbackRetentionTests(TestCase):
    def setUp(self):
        self.expired = UserQuestion.objects.create(
            contact_email="expired@example.com",
            question_text="Старое обработанное обращение",
            telegram_status=UserQuestion.DeliveryStatus.SENT,
        )
        self.pending = UserQuestion.objects.create(
            contact_email="pending@example.com",
            question_text="Старое неотправленное обращение",
            telegram_status=UserQuestion.DeliveryStatus.PENDING,
        )
        self.expired_applicant = ApplicantProfile.objects.create(
            name="Иван",
            telephone_number="+7 999 123-45-67",
            telegram_status=UserQuestion.DeliveryStatus.SENT,
        )
        old_date = timezone.now() - timedelta(days=31)
        UserQuestion.objects.filter(pk__in=(self.expired.pk, self.pending.pk)).update(
            created_at=old_date
        )
        ApplicantProfile.objects.filter(pk=self.expired_applicant.pk).update(
            created_at=old_date
        )

    def test_cleanup_is_dry_run_by_default(self):
        call_command("cleanup_feedback_data", days=30)

        self.assertEqual(UserQuestion.objects.count(), 2)
        self.assertTrue(ApplicantProfile.objects.filter(pk=self.expired_applicant.pk).exists())

    def test_cleanup_deletes_only_delivered_expired_questions(self):
        call_command("cleanup_feedback_data", days=30, delete=True)

        self.assertFalse(UserQuestion.objects.filter(pk=self.expired.pk).exists())
        self.assertTrue(UserQuestion.objects.filter(pk=self.pending.pk).exists())
        self.assertFalse(ApplicantProfile.objects.filter(pk=self.expired_applicant.pk).exists())


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


class AnalyticsIntegrationTests(TestCase):
    @override_settings(DEBUG=False, YANDEX_METRIKA_ID=111433025)
    def test_production_page_contains_consent_banner_and_analytics_script(self):
        response = self.client.get(reverse("job:privacy"))

        self.assertContains(response, 'data-counter-id="111433025"')
        self.assertContains(response, "job/js/analytics.js")
        self.assertNotContains(response, "mc.yandex.ru/metrika/tag.js")

    @override_settings(DEBUG=True, YANDEX_METRIKA_ID=111433025)
    def test_debug_page_does_not_include_analytics(self):
        response = self.client.get(reverse("job:privacy"))

        self.assertNotContains(response, "data-analytics-consent")
        self.assertNotContains(response, "job/js/analytics.js")

    def test_privacy_policy_describes_analytics_and_disabled_webvisor(self):
        response = self.client.get(reverse("job:privacy"))

        self.assertContains(response, "Яндекс Метрику")
        self.assertContains(response, "Вебвизор отключён")


@override_settings(
    BACKUP_S3_BUCKET="mgroup-backups",
    BACKUP_S3_PREFIX="production",
    BACKUP_S3_ENDPOINT_URL="https://storage.yandexcloud.net",
    BACKUP_S3_ACCESS_KEY_ID="backup-key",
    BACKUP_S3_SECRET_ACCESS_KEY="backup-secret",
    BACKUP_DATABASE_TIMEOUT_SECONDS=60,
    BACKUP_PGSSLMODE="prefer",
    AWS_STORAGE_BUCKET_NAME="mgroup",
)
class PostgreSQLBackupTests(SimpleTestCase):
    database_settings = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "production",
            "USER": "backup_user",
            "PASSWORD": "secret-password",
            "HOST": "database.internal",
            "PORT": "5432",
        }
    }

    @patch("job.management.commands.backup_postgres.boto3.client")
    @patch("job.management.commands.backup_postgres.Command._verify_dump")
    @patch("job.management.commands.backup_postgres.Command._create_dump")
    def test_backup_is_verified_and_uploaded_to_separate_bucket(
        self, create_dump, verify_dump, boto_client
    ):
        create_dump.side_effect = lambda database, path: path.write_bytes(b"backup")
        client = boto_client.return_value

        def verify_uploaded_object(**kwargs):
            upload = client.upload_file.call_args
            return {
                "ContentLength": Path(upload.args[0]).stat().st_size,
                "Metadata": {},
            }

        client.head_object.side_effect = verify_uploaded_object

        with patch(
            "job.management.commands.backup_postgres.settings.DATABASES",
            self.database_settings,
        ):
            with self.assertLogs(
                "job.management.commands.backup_postgres", level="WARNING"
            ):
                call_command("backup_postgres")

        create_dump.assert_called_once()
        verify_dump.assert_called_once()
        client.upload_file.assert_called_once()
        self.assertEqual(client.upload_file.call_args.args[1], "mgroup-backups")
        self.assertIn("/postgresql/", client.upload_file.call_args.args[2])

    @override_settings(BACKUP_S3_BUCKET="mgroup")
    def test_backup_rejects_media_bucket_as_destination(self):
        with self.assertRaisesMessage(
            CommandError, "backup bucket must be separate"
        ):
            with patch(
                "job.management.commands.backup_postgres.settings.DATABASES",
                self.database_settings,
            ):
                call_command("backup_postgres")

    @patch("job.management.commands.backup_object_storage.boto3.client")
    def test_object_storage_backup_copies_versions_and_uploads_manifest(
        self, boto_client
    ):
        client = boto_client.return_value
        paginator = client.get_paginator.return_value
        paginator.paginate.return_value = [
            {
                "Contents": [
                    {
                        "Key": "photos/one.webp",
                        "Size": 100,
                        "ETag": '"etag-one"',
                        "LastModified": timezone.now(),
                    },
                    {
                        "Key": "photos/two.webp",
                        "Size": 200,
                        "ETag": '"etag-two"',
                        "LastModified": timezone.now(),
                    },
                ]
            }
        ]

        def head_object(**kwargs):
            if "/manifests/" in kwargs["Key"]:
                uploaded_manifest = client.put_object.call_args.kwargs
                return {
                    "ContentLength": len(uploaded_manifest["Body"]),
                    "Metadata": {},
                }
            for copied_object in client.copy_object.call_args_list:
                if copied_object.kwargs["Key"] == kwargs["Key"]:
                    source_key = copied_object.kwargs["CopySource"]["Key"]
                    return {
                        "ContentLength": 100 if source_key.endswith("one.webp") else 200
                    }
            raise ClientError(
                {
                    "Error": {"Code": "404"},
                    "ResponseMetadata": {"HTTPStatusCode": 404},
                },
                "HeadObject",
            )

        client.head_object.side_effect = head_object

        with self.assertLogs(
            "job.management.commands.backup_object_storage", level="WARNING"
        ):
            call_command("backup_object_storage")

        self.assertEqual(client.copy_object.call_count, 2)
        client.put_object.assert_called_once()
        manifest = json.loads(client.put_object.call_args.kwargs["Body"])
        self.assertEqual(manifest["object_count"], 2)
        self.assertEqual(manifest["total_size"], 300)
        self.assertEqual(manifest["source_bucket"], "mgroup")


class ProductionBackupCommandTests(SimpleTestCase):
    @patch("job.management.commands.backup_production.call_command")
    def test_combined_backup_runs_database_then_object_storage(self, command):
        call_command("backup_production")

        self.assertEqual(
            command.call_args_list,
            [
                call("backup_postgres"),
                call("backup_object_storage"),
            ],
        )
