namespace = 'job'

menu = {
    'about': {'title': 'О нас', 'url_name': f'{namespace}:article_list'},
    'services': {
        'title': 'Услуги',
        'url_name': f'{namespace}:post_list',
        'submenus': [
            {'title': 'Покраска', 'url_name': f'{namespace}:article_list'},
            {'title': 'Очистка', 'url_name': f'{namespace}:article_list'},
            {'title': 'Обработка', 'url_name': f'{namespace}:article_list'},]
    },
    'articles': {'title': 'Статьи', 'url_name': f'{namespace}:article_list'},
    'projects': {'title': 'Проекты', 'url_name': f'{namespace}:article_list'},
}

services = {

}

class DataMixin:
    paginate_by = 3
    title_page = None
    extra_context = {}
    cat_selected = None

    def __init__(self):
        if self.title_page:
            self.extra_context['title'] = self.title_page
        if self.cat_selected is not None:
            self.extra_context['cat_selected'] = self.cat_selected

    def get_mixin_context(self, context, **kwargs):
        context['cat_selected'] = None
        context.update(**kwargs)
        return context
