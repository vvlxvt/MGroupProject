from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.contrib import admin
from django.urls import path, include
from job.sitemaps import project_sitemap, article_sitemap, post_sitemap
from job.views import page_not_found
from django.views.generic import TemplateView

sitemaps_dict = {
    'post': post_sitemap,
    'projects': project_sitemap,
    'articles': article_sitemap,
}


urlpatterns = [
    path("admin/", admin.site.urls),
    path("test404/", page_not_found, name="test_404"),
    path("", include("job.urls", namespace="job")),
    # path('__debug__/', include('debug_toolbar.urls')),
    path("sitemap.xml",sitemap,{"sitemaps": sitemaps_dict},name="sitemap",),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
]

if settings.DEBUG:
    # # маршрут к медиафайлам в режиме отладки. В боевом режиме сервер сам знает путь
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




handler404 = page_not_found