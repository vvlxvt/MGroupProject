import re

import requests, json
from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.postgres.search import SearchVector, SearchQuery, TrigramSimilarity
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from bot_instance import bot, TOKEN, chat_id
from taggit.models import Tag
from .forms import ContactForm
from .models import Post, Article, Project, Category, Contact
from .utils import DataMixin, generate_verification_code
from .models import Contact
import redis

redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=1)  # Используем базу 1

class DynamicPostListView(DataMixin, ListView):
    title_page = 'Наши услуги'
    model = Post
    context_object_name = 'posts'
    template_name = 'job/post/list.html'
    allow_empty = True  # Позволяет показывать пустой список, если постов нет

    def get_queryset(self):
        queryset = Post.published.all().select_related('cat').prefetch_related('tags')

        # Фильтрация по категории
        cat_slug = self.request.GET.get('category')
        if cat_slug:
            queryset = queryset.filter(cat__slug=cat_slug)

        # Фильтрация по тегу
        tag_slug = self.request.GET.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        # Поиск по запросу
        query = self.request.GET.get('query')
        if query:
            search_vector = (
                SearchVector('title', weight='A', config='russian') +
                SearchVector('body', weight='B', config='russian')
            )
            search_query = SearchQuery(query, config='russian')
            queryset = queryset.annotate(
                search=search_vector,
                similarity=TrigramSimilarity('title', query)
            ).filter(
                Q(search=search_query) | Q(similarity__gt=0.1)
            ).order_by('-similarity')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Доступ к фильтрующим параметрам
        cat_slug = self.request.GET.get('category')
        tag_slug = self.request.GET.get('tag')
        query = self.request.GET.get('query')

        # Добавляем категории и теги в контекст
        context['categories'] = Category.objects.all()
        context['tags'] = Tag.objects.all()

        # Устанавливаем заголовок и мета-описание
        if cat_slug:
            category = Category.objects.filter(slug=cat_slug).first()
            if category:
                context['title'] = f"Категория: {category.name}"
                context['meta_description'] = f"Отображение постов в категории {category.name}."

        if tag_slug:
            tag = Tag.objects.filter(slug=tag_slug).first()
            if tag:
                context['title'] = f"Тег: {tag.name}"
                context['meta_description'] = f"Результат поиска постов, содержащих тэги: {tag.name}."

        if query:
            context['query'] = query
            context['title'] = f"Результаты поиска: {query}"
            context['meta_description'] = f"Результат поиска постов, содержащих слово: {query}."

        return context


class AboutView(DataMixin,TemplateView):
    template_name = "job/post/about.html"
    title_page = 'О нас'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['meta_description'] = f"Информация о нашей компании"
        # context["latest_articles"] = Article.objects.all()[:5]
        return context


def post_detail(request, year, month, day, post):
    # извлекаем пост по id
    post = get_object_or_404(Post, status=Post.Status.PUBLISHED,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    # Набор запросов QuerySet values_list() возвращает кортежи со значениями заданных полей
    post_tags_ids = post.tags.values_list('id', flat=True) # параметр flat=True, чтобы получить одиночные значения
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags','-publish')[:4]
    return render(request,'job/post/detail.html',
                  {'post': post,
                   'title': post,
                   'similar_posts':similar_posts})


# def post_search(request):
#     form = SearchForm()
#     query = None
#     results = []
#
#     if 'query' in request.GET: # использую GET чтобы результат отображался в строке адреса и им можно было делиться
#         form = SearchForm(request.GET)
#         if form.is_valid():
#             query = form.cleaned_data['query']
#             print(f"Поисковый запрос: {query}")
#             search_vector = (SearchVector('title', weight='A', config='russian')
#                              + SearchVector('body', weight='B',config='russian'))
#             # выполняем поиск опубликованных постов сформированного с использованием полей title и body
#             #  с помощью прикладного экземпляра SearchVector
#             search_query = SearchQuery(query, config='russian') # класс SearchQuery транслирует термин в объект поискового запроса
#             # print(search_query)
#             # results = (Post.published
#             #            .annotate(search=search_vector,rank=SearchRank(search_vector,search_query))
#             #            .filter(rank__gte=0.3)
#             #            .order_by('-rank'))
#             results = (Post.published.annotate(similarity=TrigramSimilarity('title', query),)
#                                        .filter(similarity__gt=0.1)
#                                        .order_by('-similarity'))
#             print(connection.queries)
#
#         return render(request, 'job/post/search.html', {
#                       'form':form, 'query':query, 'results':results, 'title': "Результаты поиска" })
#     else:
#         return render(request, 'job/post/search.html')


class ArticleListView(DataMixin, ListView):
    model = Article
    title_page = 'Статьи'
    context_object_name = 'articles'
    template_name = 'job/article/article_list.html'


    def get_queryset(self):
        return Article.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['meta_description'] = f"Популярные статьи о способах обработки поверхностей"

        return context

def article_detail(request,article):
    article = get_object_or_404(Article, slug=article)
    context={'title': article,
            'article': article,
             'meta_description': article,}
    return render(request,'job/article/article_detail.html',context)

class ProjectListView(DataMixin, ListView):
    title_page = 'Выполненные проекты'
    context_object_name = 'projects'
    paginate_by = 20  # количество объектов на страницу
    template_name = 'job/project/project_list.html'

    def get_queryset(self):
        # Выбираем только нужные поля
        return Project.objects.only('id', 'title', 'lat', 'lng', 'publish')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Используем объектный список из get_queryset
        projects = self.object_list

        # Генерируем список локаций для карты
        locations_list = [
            {'id': project.id, 'position': {'lat': project.lat, 'lng': project.lng}, 'title': project.title}
            for project in projects
        ]

        # Добавляем данные в контекст
        context['locations_json'] = json.dumps(locations_list, cls=DjangoJSONEncoder)
        context['google_maps_api_key'] = settings.GOOGLE_MAPS_API_KEY
        context['meta_description'] = f"Наши выполненные проекты с координатами на карте Google"

        return context



def project_detail(request,project):
    project = get_object_or_404(Project, slug=project)
    context = {'project': project,
               'title': project,
               'meta_description': f"Выполненный проект {project}",}
    return render(request,'job/project/project_detail.html',context)

def home(request):
    posts = Post.published.all()
    locations = Project.objects.all()
    locations_list = [{'id': place.id, 'position': {'lat': place.lat, 'lng': place.lng}, 'title': place.title} for place in locations]
    # title = 'МалярГрупп'
    title = '<span>ГАРАНТИЯ НА РАБОТЫ</span> <span>ЦЕНА ИЗВЕСТНА ЗАРАНЕЕ</span> <span>ДИЗАЙН ПРОЕКТ</span>'
    context = {
        'posts': posts,
        'title': title,
        'locations': locations,  # Для вывода списка проектов
        'locations_json': json.dumps(locations_list),  # Для передачи в JS
    }

    return render(request, 'job/post/index.html', context)

def page_not_found(request, exception):
    return render(request, '404.html', status=404)


def contacts(request):
    title = 'Напишите нам Ваши вопросы и мы постараемся помочь'
    context = {'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
               'title': title,
    }
    return render(request, 'job/post/contacts.html',context)



# Функция для отправки сообщения и фото в Telegram
def send_telegram_message(username, user_id, telegram_message, photo=None):
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID

    # URL для отправки текстового сообщения
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # URL для отправки файла
    telegram_url_photo = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    link = f'User ID: <code>{user_id}</code> (User has no username)'
    caption = f"{telegram_message} от пользователя {username} c {link}"
    try:
        if photo:
            files = {'photo': photo}
            requests.post(telegram_url_photo, data={'chat_id': user_id,
                                                    'caption': caption,
                                                    'parse_mode': 'HTML'}, files=files)
        else:
            requests.post(telegram_url, data={'chat_id': user_id,
                                              'text': caption,
                                              'parse_mode': 'HTML'})
        return True

    except Exception as e:
        print(f"Ошибка при отправке в Telegram: {e}")
        return False



@require_http_methods(["POST"])
def generate_code_view(request):
    tg_username = request.POST.get('tg_username')
    if not re.match(r'^[a-zA-Z0-9_]+$', tg_username):
        return JsonResponse(
            {'success': False, 'message': 'Username должен содержать только латинские буквы, цифры и _.'})
    request.session['tg_username'] = tg_username
    code = str(generate_verification_code())
    redis_client.hset(tg_username, "code", code)
    redis_client.expire(tg_username, 300)
    name = request.POST.get('name')
    telegram_url = f"https://t.me/mgrup24_bot?start={tg_username}"
    try:
        contact = Contact.objects.get(tg_username=tg_username)
        if contact.name != name:
            return JsonResponse({'success': False, 'message': 'Имя пользователя не совпадает с Telegram username.'})
        else:
            return JsonResponse({"success": True, "message": "Пользователь успешно найден.", 'email': contact.email,
                "show_pass_key": False})
    except Contact.DoesNotExist:  # Исправлено: указана модель Contact
        return JsonResponse(
            {'success': True, 'message': "Требуется верификация.",
             "redirect": telegram_url, "show_pass_key": True})


@require_http_methods(["POST"])
def verify_code_view(request):
    tg_username = request.POST.get('tg_username')
    name = request.POST.get('name')
    code = request.POST.get('code')
    # Проверка наличия данных
    if not tg_username or not code:
        return JsonResponse({'success': False, 'message': 'Необходимо указать Telegram username и код.'})
    redis_value = redis_client.hget(tg_username,'code')
    print(f'{redis_value} - получил')
    if redis_value is not None:
        if redis_value.decode('utf-8') == code:
            print('код совпал')
            tg_id = redis_client.hget(tg_username,'user_id')
            try:
                contact = Contact.objects.create(tg_username=tg_username, name=name, verified=True, tg_id=tg_id)
            except IntegrityError:
                return JsonResponse({'status': 'error', 'message': 'Пользователь с вашим id уже существует'})
            return JsonResponse({'status': 'verified', 'message': 'Вы верифицированны. Пожалуйста напишите вопрос'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Неверный код'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Истек срок действия ключа'})


@require_http_methods(["POST"])
def save_message_view(request):
    tg_username = request.session.get('tg_username')
    photo = request.FILES.get('photo')
    try:
        contact = Contact.objects.get(tg_username=tg_username)
        if contact.verified == True:
            contact.email = request.POST.get('email')
            contact.message = request.POST.get('message')
            if photo:
                contact.photo = photo
            send_telegram_message(contact.tg_username, contact.tg_id, contact.message, photo)
            contact.save()
        return JsonResponse({'success': True, 'message': 'Сообщение отправлено!'})
    except Contact.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Пользователь не верифицирован.'})
