import json
import requests
from datetime import datetime

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import make_aware
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.generic import ListView, TemplateView, DetailView
from django.contrib.postgres.search import SearchVector, SearchQuery, TrigramSimilarity

from taggit.models import Tag

from .models import Post, Article, Project, Category, UserProfile, UserQuestion
from .forms import UserQuestionForm, UserProfileForm
from .utils import (
    DataMixin,
    advantages,
    partners,
    chunk_list,
    verify_telegram_auth,
    save_user_photo,
    send_telegram_message,
)


class DynamicPostListView(DataMixin, ListView):
    title_page = "Наши услуги"
    model = Post
    context_object_name = "posts"
    template_name = "job/post/list.html"
    allow_empty = True  # Позволяет показывать пустой список, если постов нет

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if queryset.count() == 1:
            post = queryset.first()
            return redirect("post_detail", post=post.slug)

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Post.published.all().select_related("cat").prefetch_related("tags")

        # Фильтрация по категории
        cat_slug = self.request.GET.get("category")
        if cat_slug:
            queryset = queryset.filter(cat__slug=cat_slug)

            print(queryset)

        # Фильтрация по тегу
        tag_slug = self.request.GET.get("tag")
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        # Поиск по запросу
        query = self.request.GET.get("query")
        if query:
            search_vector = SearchVector(
                "title", weight="A", config="russian"
            ) + SearchVector("body", weight="B", config="russian")
            search_query = SearchQuery(query, config="russian")
            queryset = (
                queryset.annotate(
                    search=search_vector, similarity=TrigramSimilarity("title", query)
                )
                .filter(Q(search=search_query) | Q(similarity__gt=0.1))
                .order_by("-similarity")
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Доступ к фильтрующим параметрам
        cat_slug = self.request.GET.get("category")
        tag_slug = self.request.GET.get("tag")
        query = self.request.GET.get("query")

        # Добавляем категории и теги в контекст
        context["categories"] = Category.objects.all()
        context["tags"] = Tag.objects.all()

        # Устанавливаем заголовок и мета-описание
        if cat_slug:
            category = Category.objects.filter(slug=cat_slug).first()
            if category:
                context["title"] = f"{category.name}"
                context["meta_description"] = (
                    f"Отображение постов в категории {category.name}."
                )

        if tag_slug:
            tag = Tag.objects.filter(slug=tag_slug).first()
            if tag:
                context["title"] = f"Тег: {tag.name}"
                context["meta_description"] = (
                    f"Результат поиска постов, содержащих тэги: {tag.name}."
                )

        if query:
            context["query"] = query
            context["title"] = f"Результаты поиска: {query}"
            context["meta_description"] = (
                f"Результат поиска постов, содержащих слово: {query}."
            )

        return context

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if queryset.count() == 1:
            post = queryset.first()
            return redirect("job:post_detail", slug=post.slug)

        return super().get(request, *args, **kwargs)


class AboutView(DataMixin, TemplateView):
    template_name = "job/post/about.html"
    title_page = "О нас"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meta_description"] = f"Информация о нашей компании"
        # context["latest_articles"] = Article.objects.all()[:5]
        return context


def post_detail(request, slug):
    # извлекаем пост по id
    post = get_object_or_404(Post, status=Post.Status.PUBLISHED, slug=slug)
    # Набор запросов QuerySet values_list() возвращает кортежи со значениями заданных полей
    post_tags_ids = post.tags.values_list(
        "id", flat=True
    )  # параметр flat=True, чтобы получить одиночные значения
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count("tags")).order_by(
        "-same_tags", "-publish"
    )[:4]
    return render(
        request,
        "job/post/detail.html",
        {"post": post, "title": post, "similar_posts": similar_posts},
    )


class ArticleListView(DataMixin, ListView):
    model = Article
    title_page = "Статьи"
    context_object_name = "articles"
    template_name = "job/article/article_list.html"

    def get_queryset(self):
        return Article.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meta_description"] = (
            f"Популярные статьи о способах обработки поверхностей"
        )
        return context


class ArticleDetailView(DetailView):
    model = Article
    template_name = "job/article/article_detail.html"
    context_object_name = "article"

    def get_queryset(self):
        return Article.objects.only("title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.object.title
        context["meta_description"] = f"Cтатья о {self.object.title}"
        context["articles"] = Article.objects.only("title")
        return context


class ProjectListView(DataMixin, ListView):
    title_page = "Выполненные проекты"
    context_object_name = "projects"
    paginate_by = 20  # количество объектов на страницу
    template_name = "job/project/project_list.html"

    def get_queryset(self):
        # Выбираем только нужные поля
        return Project.objects.only("id", "slug", "title", "lat", "lng", "publish")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Используем объектный список из get_queryset
        projects = self.object_list

        # Генерируем список локаций для карты
        locations_list = [
            {
                "id": project.id,
                "position": {"lat": project.lat, "lng": project.lng},
                "title": project.title,
            }
            for project in projects
        ]

        # Добавляем данные в контекст
        context["locations_json"] = json.dumps(locations_list, cls=DjangoJSONEncoder)
        context["google_maps_api_key"] = settings.GOOGLE_MAPS_API_KEY
        context["meta_description"] = (
            f"Наши выполненные проекты с координатами на карте Google"
        )

        return context


class ProjectCardView(DetailView):
    model = Project
    template_name = "job/project/project_card.html"  # нужно в кавычках
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["id"] = self.object.id
        context["meta_description"] = f"Выполненный проект {self.object.title}"
        return context


class ProjectDetailView(DetailView):
    model = Project
    template_name = "job/project/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        return Project.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.object.title
        context["meta_description"] = f"Выполненный проект {self.object.title}"
        return context


def home(request):
    # posts = Post.published.all()
    posts = Post.published.prefetch_related("postarticle_set__article").all()
    title = "МЫ РАДЫ ПРИВЕТСТВОВАТЬ ВАС НА САЙТЕ КОМПАНИИ"
    projects = Project.objects.only("title", "slug")
    grouped_projects = {
        "lg": chunk_list(list(projects), 3),  # По 3 для больших экранов
        "md": chunk_list(list(projects), 2),  # По 2 для средних экранов
        "sm": chunk_list(list(projects), 1),  # По 1 для мобильных
    }
    # projects = Project.objects.all()
    context = {
        "posts": posts,
        "title": title,
        "grouped_projects": grouped_projects,
        "projects": projects,
        "partners": partners,
        "advantages": advantages,
    }

    return render(request, "job/post/index.html", context)


def page_not_found(request, exception):
    return render(request, "404.html", status=404)


def contacts(request):
    title = "Напишите нам Ваши вопросы и мы постараемся помочь"

    user_data = request.session.get("user", {})
    telegram_id = user_data.get("id")

    user = None
    if telegram_id:
        try:
            user = UserProfile.objects.get(telegram_id=telegram_id)
        except UserProfile.DoesNotExist:
            pass

    # Инициализация формы с уже сохранёнными данными
    if user:
        if not user.email:
            user.email = user_data.get("email", "")
        if not user.city:
            user.city = user_data.get("city", "")

    user_form = UserProfileForm(instance=user)
    print(user_form.initial)
    q_form = UserQuestionForm()

    context = {
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
        "title": title,
        "user_form": user_form,
        "q_form": q_form,
    }
    return render(request, "job/post/contacts.html", context)


from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_protect


@require_GET
def telegram_auth_view(request):
    user_data = request.GET.dict()

    # Проверка Telegram-аутентификации
    if not verify_telegram_auth(request.META["QUERY_STRING"]):
        return JsonResponse({"error": "Invalid Telegram authentication"}, status=403)

    try:
        timestamp = int(user_data.get("auth_date", 0))
        calendar_time = make_aware(datetime.utcfromtimestamp(timestamp))
    except (ValueError, TypeError):
        return JsonResponse({"error": "Некорректная дата аутентификации"}, status=400)

    # Создаём пользователя, если не существует
    telegram_id = int(user_data.get("id", 0))
    user, created = UserProfile.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            "username": user_data.get("username", ""),
            "first_name": user_data.get("first_name", ""),
            "last_name": user_data.get("last_name", ""),
            "auth_date": calendar_time,
        },
    )

    save_user_photo(user)

    # Сохраняем в сессию
    request.session["user"] = {
        "id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "auth_date": user.auth_date.strftime("%Y-%m-%d %H:%M"),
        "email": user.email,
        "city": user.city,
    }

    return redirect("/contacts/")


@csrf_protect
@require_POST
def submit_question(request):
    q_form = UserQuestionForm(request.POST, request.FILES)

    if q_form.is_valid():
        telegram_id = request.POST.get("telegram_id")
        try:
            user = UserProfile.objects.get(telegram_id=telegram_id)
        except UserProfile.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Пользователь не найден!"}, status=404
            )

        # Сохраняем вопрос
        question = q_form.save(commit=False)
        question.user = user
        question.save()

        # Обновляем email и city, если переданы
        email = request.POST.get("email")
        city = request.POST.get("city")
        if email and email != user.email:
            user.email = email
        if city and city != user.city:
            user.city = city
        user.save()

        send_telegram_message(question)
        return JsonResponse({"success": True, "message": "Вопрос успешно отправлен!"})

    return JsonResponse({"success": False, "error": q_form.errors})


def vacancies(request):
    title = "Открытые вакансии"
    return render(request, "job/post/vacancies.html", {"title": title})
