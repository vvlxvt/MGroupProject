from django.urls import path
from . import views

app_name = 'job'  # определяю пространство имен для приложения

urlpatterns = [
    path('', views.post_list, name='post_list'),
    # path('',views.PostListView.as_view(), name = 'post_list'),
    path('<int:year>/<int:month>/<int:day>/<slug:post>/', views.post_detail, name='post_detail'),
    path('<int:post_id>/share/', views.post_share, name='post_share'),
    path('<int:post_id>/comment/', views.post_comment, name = 'post_comment'),
    path('<slug:tag_slug>/', views.post_list, name = 'post_list_by_tag'),
]
