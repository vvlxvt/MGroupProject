from django.urls import path
from . import views
from .feeds import LatestPostsFeed

app_name = 'job'  # определяю пространство имен для приложения

urlpatterns = [
    path('', views.home, name='home'),
    path('services',views.DynamicPostListView.as_view(), name = 'post_list'),
    path('text_us/', views.text_us, name='text_us'),
    path('contact/', views.contact_view, name='contact'),
    path('about/', views.AboutView.as_view(), name = 'about'),
    path('articles/',views.ArticleListView.as_view(), name = 'article_list'),
    path('projects/',views.ProjectListView.as_view(), name = 'projects'),
    path('<slug:article>/', views.article_detail, name='article_detail'),
    path('<int:year>/<int:month>/<int:day>/<slug:post>/', views.post_detail, name='post_detail'),
    path('<int:post_id>/share/', views.post_share, name='post_share'),
    path('<int:post_id>/comment/', views.post_comment, name = 'post_comment'),
    path('feed/', LatestPostsFeed(), name='post_feed'),

]

