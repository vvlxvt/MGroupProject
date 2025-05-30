from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from .feeds import LatestPostsFeed

app_name = "job"  # определяю пространство имен для приложения

urlpatterns = [  # it is URLconf
    path("", views.home, name="home"),
    path("services/", views.DynamicPostListView.as_view(), name="post_list"),
    # path('telegram-auth/', views.telegram_auth_view, name='telegram_auth'),
    path("submit-question/", views.submit_question, name="submit_question"),
    path("contacts/", views.contacts, name="contacts"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("articles/", views.ArticleListView.as_view(), name="article_list"),
    path("projects/", views.ProjectListView.as_view(), name="projects"),
    path("ajax/card/<int:pk>/", views.ProjectCardView.as_view(), name="ajax_load_card"),
    path(
        "articles/<slug:slug>/",
        views.ArticleDetailView.as_view(),
        name="article_detail",
    ),
    path(
        "projects/<slug:slug>/",
        views.ProjectDetailView.as_view(),
        name="project_detail",
    ),
    path("vacancies/", views.vacancies, name="vacancies"),
    path("feed/", LatestPostsFeed(), name="post_feed"),
    path("callback/", views.telegram_auth_view, name="callback"),
    path("<slug:slug>/", views.post_detail, name="post_detail"),
]
