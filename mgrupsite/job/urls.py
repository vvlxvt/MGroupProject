from django.urls import path
from . import views
from .feeds import LatestPostsFeed
from .views import CategoryView

app_name = 'job'  # определяю пространство имен для приложения

urlpatterns = [
    path('services',views.PostListView.as_view(), name = 'post_list'),
    path('category/<slug:cat_slug>/', CategoryView.as_view(), name='category'),
    path('home/', views.home, name='home'),
    path('contact/', views.contact_view, name='contact'),
    path('about/', views.AboutView.as_view(), name = 'about'),
    path('articles/',views.ArticleListView.as_view(), name = 'article_list'),
    path('projects/',views.ProjectListView.as_view(), name = 'projects'),
    # path('articles/', views.article_list, name='article_list'),
    path('<slug:article>/', views.article_detail, name='article_detail'),
    # path('tag/<slug:tag_slug>/', views.post_list, name = 'post_list_by_tag'),
    path('<int:year>/<int:month>/<int:day>/<slug:post>/', views.post_detail, name='post_detail'),
    path('<int:post_id>/share/', views.post_share, name='post_share'),
    path('<int:post_id>/comment/', views.post_comment, name = 'post_comment'),
    path('feed/', LatestPostsFeed(), name='post_feed'),
    path('search/', views.post_search, name='post_search'),
]
