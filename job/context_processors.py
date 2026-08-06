from django.conf import settings
from django.core.cache import cache

from job.models import Category


MENU_CATEGORIES_CACHE_KEY = "navigation:categories:v1"


def get_menu_categories():
    return cache.get_or_set(
        MENU_CATEGORIES_CACHE_KEY,
        lambda: list(
            Category.objects.order_by("number").values("name", "slug")
        ),
        timeout=settings.MENU_CACHE_TIMEOUT,
    )


def menu_context(request):
    namespace = "job"
    categories = get_menu_categories()
    menu = {
        "about": {"title": "О нас", "url_name": f"{namespace}:about"},
        "services": {
            "title": "Услуги",
            "url_name": f"{namespace}:post_list",
            "submenus": [
                {
                    "title": category["name"],
                    "url_name": f"{namespace}:post_list",
                    "slug": category["slug"],
                }
                for category in categories
            ],
        },
        "articles": {"title": "Статьи", "url_name": f"{namespace}:article_list"},
        "projects": {"title": "Проекты", "url_name": f"{namespace}:projects"},
        "calculator": {"title": "Вакансии", "url_name": f"{namespace}:vacancies"},
        "contacts": {"title": "Контакты", "url_name": f"{namespace}:contacts"},
    }
    return {"menu": menu, "facemenu": menu["services"].get("submenus", [])}


def canonical_url(request):
    base_url = settings.CANONICAL_BASE_URL or f"{request.scheme}://{request.get_host()}"
    canonical = f"{base_url}{request.path}"

    page = request.GET.get("page")
    if page and page.isdigit() and int(page) > 1:
        canonical = f"{canonical}?page={page}"

    return {"canonical_url": canonical}
