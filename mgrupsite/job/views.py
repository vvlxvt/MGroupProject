from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, TemplateView
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity
from django.core.mail import send_mail
from .forms import EmailPostForm, CommentForm, SearchForm
from django.views.decorators.http import require_POST
from .models import Post, Article, Project, Category
from taggit.models import Tag
from django.db.models import Count
from .utils import DataMixin, services


class PostListView(DataMixin, ListView):
    title_page = 'Наши услуги'
    model = Post
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'job/post/list.html'

    def get_queryset(self):
        return Post.published.all()


class CategoryView(DataMixin, ListView):
    context_object_name = 'posts'
    template_name = 'job/post/category.html'

    def get_queryset(self):
        return Post.published.filter(cat__slug=self.kwargs['cat_slug']).select_related('cat')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cat = context['posts'][0].cat
        # Динамически обновляем title_page с выбранной категорией
        context['title_page'] = f'Наши услуги - {cat.name}'
        return self.get_mixin_context(context, title=f'Категория - {cat.name}', cat_selected=cat.pk)


class AboutView(DataMixin,TemplateView):
    template_name = "job/post/about.html"
    title_page = 'О нас'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["latest_articles"] = Article.objects.all()[:5]
        return context


def post_detail(request, year, month, day, post):
    # извлекаем пост по id
    post = get_object_or_404(Post, status=Post.Status.PUBLISHED,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    # Список активных комментариев к этому посту
    comments = post.comments.filter(active=True)
    # Форма для комментирования пользователями
    form = CommentForm()
    # Набор запросов QuerySet values_list() возвращает кортежи со значениями заданных полей
    post_tags_ids = post.tags.values_list('id', flat=True) # параметр flat=True, чтобы получить одиночные значения
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags','-publish')[:4]
    return render(request,'job/post/detail.html',
                  {'post': post,'comments':comments,'form':form, 'similar_posts':similar_posts})

def post_share(request, post_id):
    post = get_object_or_404(Post,id=post_id, status=Post.Status.PUBLISHED)
    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data # cleaned_data будет содержать только валидные поля.
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} рекомендует тебе прочесть {post.title}"
            message = (f"Прочитай {post.title} на {post_url}\n\n {cd['name']}\'s comments: {cd['comments']}")
            send_mail(subject, message, 'vvlxvt@yandex.ru', [cd['to']])
            sent = True
    else:
        form = EmailPostForm() # иначе отображается пустая форма, тк запрос GET

    return render(request, 'job/post/share.html',{'post':post, 'form':form, 'sent':sent})



@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post,id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
    return render(request,'job/post/comment.html',{'post':post, 'form':form, 'comment':comment})


def post_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET: # использую GET чтобы результат отображался в строке адреса и им можно было делиться
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = (SearchVector('title', weight='A', config='russian')
                             + SearchVector('body', weight='B',config='russian'))
            # выполняем поиск опубликованных постов сформированного с использованием полей title и body
            #  с помощью прикладного экземпляра SearchVector
            search_query = SearchQuery(query, config='russian') # класс SearchQuery транслирует термин в объект поискового запроса
            # results = (Post.published.annotate(search=search_vector,rank=SearchRank(search_vector,search_query))
            #            .filter(rank__gte=0.3).order_by('-rank'))
            results = (Post.published.annotate(similarity=TrigramSimilarity('title', query),)
                                       .filter(similarity__gt=0.1)
                                       .order_by('-similarity'))

    return render(request, 'job/post/search.html', {
                  'form':form, 'query':query, 'results':results})


class ArticleListView(DataMixin, ListView):
    model = Article
    title_page = 'Статьи'
    context_object_name = 'articles'
    template_name = 'job/article/article_list.html'

    def get_queryset(self):
        return Article.objects.all()

class ProjectListView(DataMixin, ListView):
    title_page = 'Выполненные проекты'
    context_object_name = 'projects'
    template_name = 'job/post/projects.html'

    def get_queryset(self):
        return Project.objects.all()

def article_detail(request,article):
    # извлекаем пост по id
    article = get_object_or_404(Article, slug=article)
    return render(request,'job/article/article_detail.html',
                  {'article': article})


def home(request):
    posts = Post.published.all()
    title = 'МалярГрупп ваш подрядчик по промышленной и коммерческой покраске'
    return render(request, 'job/post/index.html',
                  {'services': services, 'posts':posts, 'title':title}, )
