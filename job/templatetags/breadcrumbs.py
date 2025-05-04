from django import template

register = template.Library()


@register.inclusion_tag("breadcrumbs.html", takes_context=True)
def breadcrumbs(context):
    request = context["request"]
    path = request.path
    parts = path.strip("/").split("/")
    breadcrumbs = [{"title": "Главная", "url": "/"}]

    accumulated_path = ""
    for i, part in enumerate(parts):
        accumulated_path += "/" + part
        name = part.replace("-", " ").capitalize()
        url = accumulated_path + "/"
        is_last = i == len(parts) - 1
        breadcrumbs.append({"title": name, "url": "" if is_last else url})

    return {"breadcrumbs": breadcrumbs}
