from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from mgrupsite.health import health_check
from job.sitemaps import (
    article_sitemap,
    post_sitemap,
    project_sitemap,
    static_sitemap,
)

sitemaps_dict = {
    "static": static_sitemap,
    "post": post_sitemap,
    "projects": project_sitemap,
    "articles": article_sitemap,
}


urlpatterns = [
    path("health/", health_check, name="health"),
    path("admin/", admin.site.urls),
    path("", include("job.urls", namespace="job")),
    # path('__debug__/', include('debug_toolbar.urls')),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps_dict},
        name="sitemap",
    ),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
]

if settings.DEBUG:
    # # маршрут к медиафайлам в режиме отладки. В боевом режиме сервер сам знает путь
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler404 = "job.views.page_not_found"
