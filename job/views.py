from datetime import datetime

from django.conf import settings
from django.contrib.postgres.search import (SearchQuery, SearchVector,
                                            TrigramSimilarity)
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponseNotFound, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.text import Truncator
from django.utils.timezone import make_aware
from django.views.generic import DetailView, ListView, TemplateView
from taggit.models import Tag

from .forms import UserProfileForm, UserQuestionForm, ApplicantProfileForm
from .models import Article, Category, Photo, Post, Project, UserProfile, UserQuestion
from .utils import (DataMixin, advantages, chunk_list, partners,
                    ExternalServiceUnavailable,
                    verify_telegram_auth, verify_recaptcha)

from django.http import JsonResponse
from django.core.exceptions import PermissionDenied, RequestDataTooBig


def build_meta_description(text, fallback):
    cleaned_text = " ".join(strip_tags(text or "").split())
    return Truncator(cleaned_text or fallback).chars(160)


def absolute_image_url(request, image=None):
    image_url = image.url if image else static("job/images/IMG_index.webp")
    return request.build_absolute_uri(image_url)


class DynamicPostListView(DataMixin, ListView):
    title_page = "Услуги по покраске, очистке, защите поверхностей"
    model = Post
    context_object_name = "posts"
    template_name = "job/post/services.html"
    allow_empty = True  # Позволяет показывать пустой список, если постов нет

    def dispatch(self, request, *args, **kwargs):
        if request.GET.get("page") == "1":
            return HttpResponsePermanentRedirect(reverse("job:post_list"))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Post.published.all().select_related("cat").prefetch_related("tags")

        # Фильтрация по категории
        cat_slug = self.request.GET.get("category")
        if cat_slug:
            queryset = queryset.filter(cat__slug=cat_slug)

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
        context["meta_description"] = (
            "Промышленная покраска, очистка, огнезащита, гидроизоляция и "
            "антикоррозийная обработка объектов в Красноярске и Сибири."
        )

        # Доступ к фильтрующим параметрам
        cat_slug = self.request.GET.get("category")
        tag_slug = self.request.GET.get("tag")
        query = self.request.GET.get("query")

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
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        paginator = context.get("paginator")

        if paginator and paginator.count == 1:
            post = context["object_list"][0]
            return redirect("job:post_detail", slug=post.slug)

        return self.render_to_response(context)


class AboutView(DataMixin, TemplateView):
    template_name = "job/post/about.html"
    title_page = "Информация о Маляр Групп"

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
        "job/post/service_detail.html",
        {
            "post": post,
            "title": post,
            "similar_posts": similar_posts,
            "meta_description": build_meta_description(
                post.body,
                f"{post.title}. Профессиональное выполнение работ компанией Маляр Групп.",
            ),
            "og_image_url": absolute_image_url(request, post.photo),
        },
    )


class ArticleListView(DataMixin, ListView):
    model = Article
    title_page = "Статьи"
    context_object_name = "articles"
    template_name = "job/article/article_list.html"

    def dispatch(self, request, *args, **kwargs):
        if request.GET.get("page") == "1":
            return HttpResponsePermanentRedirect(reverse("job:article_list"))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Article.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meta_description"] = (
            f"Статьи о способах обработки поверхностей: покраска, очистка"
        )
        return context


class ArticleDetailView(DetailView):
    model = Article
    template_name = "job/article/article_detail.html"
    context_object_name = "article"

    def get_queryset(self):
        return Article.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.object.title
        context["meta_description"] = f"Cтатья о {self.object.title}"
        context["articles"] = Article.objects.only("id", "title", "slug")
        return context


class ProjectListView(DataMixin, ListView):
    title_page = "Наши проекты: покраска, очистка, защита объектов"
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
        context["locations"] = locations_list
        context["google_maps_api_key"] = settings.GOOGLE_MAPS_API_KEY
        context["meta_description"] = (
            "Выполненные проекты Маляр Групп по промышленной покраске, очистке, "
            "антикоррозийной защите и огнезащите объектов в Сибири."
        )
        return context


class ProjectCardView(DetailView):
    model = Project
    template_name = "job/project/project_card.html"  # нужно в кавычках
    context_object_name = "project"

    def get_queryset(self):
        return with_project_cover(Project.objects.all())

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
        context["meta_description"] = build_meta_description(
            self.object.body,
            f"Выполненный проект «{self.object.title}»: описание работ и фотографии объекта.",
        )
        return context


def home(request):
    # posts = Post.published.all()
    posts = Post.published.prefetch_related("postarticle_set__article").all()
    title = "Промышленная покраска, антикоррозийная защита, теплоизоляция | Маляр Групп"
    meta_description = "Комплексные услуги: промышленная покраска, антикоррозийная защита, пескоструй, теплоизоляция. Работаем по всей Сибири. Маляр Групп."
    projects = with_project_cover(Project.objects.only("title", "slug"))
    grouped_projects = {
        "lg": chunk_list(list(projects), 3),  # По 3 для больших экранов
        "md": chunk_list(list(projects), 2),  # По 2 для средних экранов
        "sm": chunk_list(list(projects), 1),  # По 1 для мобильных
    }
    # projects = Project.objects.all()
    context = {
        "posts": posts,
        "title": title,
        "meta_description": meta_description,
        "grouped_projects": grouped_projects,
        "projects": projects,
        "partners": partners,
        "advantages": advantages,
    }

    return render(request, "job/post/index.html", context)


def with_project_cover(queryset):
    cover_photo = Photo.objects.only("project_id", "image").order_by("pk")[:1]
    return queryset.prefetch_related(
        Prefetch("photos", queryset=cover_photo, to_attr="cover_photos")
    )


def page_not_found(request, exception):
    context = {"title": "Ошибка 404 — Страница не найдена"}
    content = render_to_string("404.html", context)
    return HttpResponseNotFound(content)


def contacts(request):
    title = "Напишите нам Ваши вопросы и мы постараемся помочь"
    meta_description = (
        "Контакты компании Маляр Групп в Красноярске: телефон, электронная почта, "
        "адрес и форма для консультации или расчёта стоимости работ."
    )

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
    q_form = UserQuestionForm()

    context = {
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
        "RECAPTCHA_SITE_KEY": settings.RECAPTCHA_SITE_KEY,
        "title": title,
        "meta_description": meta_description,
        "user_form": user_form,
        "q_form": q_form,
    }
    return render(request, "job/post/contacts.html", context)


from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST


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
    try:
        # reCAPTCHA
        verify_recaptcha(
            token=request.POST.get("recaptcha_token"),
            action="contact_form",
        )

        form = UserQuestionForm(request.POST, request.FILES)

        if not form.is_valid():
            return JsonResponse(
                {
                    "success": False,
                    "errors": {
                        field: errors[0]
                        for field, errors in form.errors.items()
                    }
                },
                status=400
            )

        user = UserProfile.objects.filter(
            telegram_id=request.POST.get("telegram_id")
        ).first()

        if not user:
            return JsonResponse(
                {"success": False, "errors": {"__all__": "Пользователь не найден"}},
                status=404
            )

        question = form.save(commit=False)
        question.user = user
        question.save()

        _update_user_profile(user, request.POST, request)

        return JsonResponse(
            {
                "success": True,
                "queued": True,
                "message": "Вопрос принят и будет отправлен специалисту.",
            },
            status=202,
        )

    except PermissionDenied as e:
        return JsonResponse(
            {"success": False, "errors": {"__all__": str(e)}},
            status=403
        )

    except RequestDataTooBig:
        return JsonResponse(
            {
                "success": False,
                "errors": {
                    "attached_photo": "Файл слишком большой. Максимум 6 MB."
                }
            },
            status=400
        )

    except ExternalServiceUnavailable:
        return JsonResponse(
            {
                "success": False,
                "message": "Сервис проверки временно недоступен. Попробуйте позже.",
            },
            status=503,
        )

def _update_user_profile(user, data, request=None): # Добавим request
    updated = False
    email = data.get("email")
    city = data.get("city")

    if email and email != user.email:
        user.email = email
        updated = True

    if city and city != user.city:
        user.city = city
        updated = True

    if updated:
        user.save(update_fields=["email", "city"])
        # Обновляем данные в сессии, чтобы при перезагрузке формы они были актуальны
        if request and "user" in request.session:
            user_session = request.session["user"]
            user_session["email"] = user.email
            user_session["city"] = user.city
            request.session.modified = True


def vacancies(request):
    title = "Открытые вакансии"
    meta_description = (
        "Вакансии компании Маляр Групп: работа для маляров антикоррозийных работ "
        "и пескоструйщиков, требования, условия и анкета соискателя."
    )
    return render(
        request,
        "job/post/vacancies.html",
        {"title": title, "meta_description": meta_description},
    )


def applicant(request):
    title = "Анкета соискателя"
    meta_description = (
        "Анкета соискателя для отклика на вакансии компании Маляр Групп. "
        "Расскажите об опыте работы и оставьте контактные данные."
    )
    success = False
    if request.method == "POST":
        form = ApplicantProfileForm(request.POST)
        if form.is_valid():
            form.save()
            success = True
            form = ApplicantProfileForm()
    else:
        form = ApplicantProfileForm()

    context = {
        "title": title,
        "meta_description": meta_description,
        "form": form,
        "success": success,
    }
    return render(request, "job/post/applicant.html", context)


