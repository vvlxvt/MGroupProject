from job.models import Category


def menu_context(request):
    namespace = "job"
    categories = Category.objects.all().order_by("number")
    menu = {
        "about": {"title": "О нас", "url_name": f"{namespace}:about"},
        "services": {
            "title": "Услуги",
            "url_name": f"{namespace}:post_list",
            "submenus": [
                {
                    "title": category.name,
                    "url_name": f"{namespace}:post_list",
                    "slug": category.slug,
                }
                for category in categories
            ],
        },
        "articles": {"title": "Статьи", "url_name": f"{namespace}:article_list"},
        "projects": {"title": "Проекты", "url_name": f"{namespace}:projects"},
        "contacts": {"title": "Контакты", "url_name": f"{namespace}:contacts"},
        "calculator": {"title": "Вакансии", "url_name": f"{namespace}:vacancies"},
    }
    return {"menu": menu, "facemenu": menu["services"].get("submenus", [])}

def canonical_url(request):
    path = request.path
    if path == '/':
        canonical = f"{request.scheme}://{request.get_host}"
    else:
        canonical = request.build_absolute_uri(path)
    return {'canonical_url': canonical}
