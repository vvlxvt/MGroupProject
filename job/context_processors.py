import json

from django.conf import settings
from django.core.cache import cache
from django.templatetags.static import static
from django.urls import reverse
from django.utils.safestring import mark_safe

from job.models import Category


MENU_CATEGORIES_CACHE_KEY = "navigation:categories:v1"


def serialize_json_ld(data):
    serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    serialized = serialized.replace("<", "\\u003C").replace(">", "\\u003E")
    serialized = serialized.replace("&", "\\u0026")
    return mark_safe(serialized)


def build_breadcrumb_json_ld(request, items):
    elements = [
        {
            "@type": "ListItem",
            "position": position,
            "name": name,
            "item": request.build_absolute_uri(url),
        }
        for position, (name, url) in enumerate(items, start=1)
    ]
    return serialize_json_ld(
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": elements}
    )


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
    endpoint_sections = {
        "about": "about",
        "post_list": "services",
        "post_detail": "services",
        "article_list": "articles",
        "article_detail": "articles",
        "projects": "projects",
        "project_detail": "projects",
        "ajax_load_card": "projects",
        "vacancies": "calculator",
        "applicant": "calculator",
        "contacts": "contacts",
    }
    endpoint = (
        request.resolver_match.url_name
        if request and request.resolver_match
        else None
    )
    return {
        "menu": menu,
        "facemenu": menu["services"].get("submenus", []),
        "active_menu_key": endpoint_sections.get(endpoint),
    }


def canonical_url(request):
    base_url = settings.CANONICAL_BASE_URL or f"{request.scheme}://{request.get_host()}"
    canonical = f"{base_url}{request.path}"

    page = request.GET.get("page")
    if page and page.isdigit() and int(page) > 1:
        canonical = f"{canonical}?page={page}"

    organization_id = f"{base_url}/#organization"
    local_business = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "@id": organization_id,
        "name": "Маляр Групп",
        "url": f"{base_url}/",
        "logo": request.build_absolute_uri(static("job/images/MG.png")),
        "image": request.build_absolute_uri(static("job/images/IMG_index.webp")),
        "telephone": "+7-391-251-67-47",
        "email": "mgrup24@mail.ru",
        "address": {
            "@type": "PostalAddress",
            "postalCode": "660011",
            "addressCountry": "RU",
            "addressRegion": "Красноярский край",
            "addressLocality": "Красноярск",
            "streetAddress": "ул. Кипрейная, д. 11",
        },
        "areaServed": ["Красноярск", "Красноярский край", "Сибирь"],
    }

    breadcrumb_labels = {
        "post_list": "Услуги",
        "article_list": "Статьи",
        "projects": "Проекты",
        "about": "О компании",
        "contacts": "Контакты",
        "vacancies": "Вакансии",
        "applicant": "Анкета соискателя",
    }
    url_name = request.resolver_match.url_name if request.resolver_match else None
    breadcrumb_json_ld = None
    if url_name in breadcrumb_labels:
        breadcrumb_json_ld = build_breadcrumb_json_ld(
            request,
            [
                ("Главная", reverse("job:home")),
                (breadcrumb_labels[url_name], request.path),
            ],
        )

    return {
        "canonical_url": canonical,
        "default_og_image_url": request.build_absolute_uri(
            static("job/images/IMG_index.webp")
        ),
        "organization_id": organization_id,
        "local_business_json_ld": serialize_json_ld(local_business),
        "breadcrumb_json_ld": breadcrumb_json_ld,
        "yandex_metrika_id": (
            settings.YANDEX_METRIKA_ID if not settings.DEBUG else None
        ),
    }
