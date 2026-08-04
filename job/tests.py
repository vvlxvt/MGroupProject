from types import SimpleNamespace

from django.test import RequestFactory, SimpleTestCase
from django.urls import get_resolver

from .models import photo_upload_to, upload_to
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
