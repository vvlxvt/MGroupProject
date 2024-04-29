from django.contrib.sitemaps.views import sitemap
from django.contrib import admin
from django.urls import path, include
from job.sitemaps import PostSitemap


sitemaps = {'post': PostSitemap}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('job/', include('job.urls', namespace='job')),
    path('__debug__/', include('debug_toolbar.urls')),
    path('sitemap.xml', sitemap, {'sitemaps':sitemaps},
         name='django.contrib.sitemaps.views.sitemap')

]
