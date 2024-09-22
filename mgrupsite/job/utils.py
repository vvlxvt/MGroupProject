namespace = 'job'

menu = {
    'about': {'title': 'О нас', 'url_name': f'{namespace}:about'},
    'services': {
        'title': 'Услуги',
        'url_name': f'{namespace}:post_list',
        'submenus': [
            {'title': 'Промышленная покраска', 'url_name': f'{namespace}:category', 'slug': 'promyshlennaya-pokraska'},
            {'title': 'Коммерческая покраска', 'url_name': f'{namespace}:category', 'slug': 'kommercheskaya-pokraska'},
            {'title': 'Обработка поверхностей', 'url_name': f'{namespace}:category', 'slug': 'obrabotka-poverhnostei'},
            {'title': 'Нанесение изоляции', 'url_name': f'{namespace}:category', 'slug': 'nanesenie-izolyatsii'},
        ]
    },
    'articles': {'title': 'Статьи', 'url_name': f'{namespace}:article_list'},
    'projects': {'title': 'Проекты', 'url_name': f'{namespace}:projects'},
}

services = {
    'industrial_painting': {'title': 'Промышленная покраска',
                            'url_name': '#',
                            'submenu': [
                                        {'title': 'Покраска металлоконструкций', 'url_name': '#'},
                                        {'title': 'Покраска помещений', 'url_name': '#'},
                                        {'title': 'Покраска фасадов', 'url_name': '#'},
                                        {'title': 'Покраска резервуаров', 'url_name': '#'}, ],
                            },
            'commercial_painting': {'title': 'Коммерческая покраска',
                                    'url_name': '#',
                                    'submenu': [
                                                {'title': 'Покраска жилых помещенией', 'url_name':'#'},
                                                {'title': 'Покраска общих помещений', 'url_name':'#'},
                                                {'title': 'Покраска офисов', 'url_name': '#'},
                                                {'title': 'Покраска квартир', 'url_name': '#'},
                                                {'title': 'Покраска деревянных поверхностей', 'url_name': '#'},
                                                {'title': 'Нанесение декоративных штукатурок', 'url_name': '#'}, ],
                                    },
            'surface_treatment': {'title': 'Обработка поверхностей',
                                  'url_name': '#',
                                  'submenu': [
                                                {'title': 'пескоструйная очистка', 'url_name': '#'},
                                                {'title': 'огнезащита', 'url_name': '#'},
                                                {'title': 'антикорозийная обработка', 'url_name': '#'}, ],
                                        },
                'insulation_application': {'title': 'Нанесение изоляции',
                                           'url_name': '#',
                                           'submenu': [
                                                {'title': 'нанесение термоизоляции', 'url_name': '#'},
                                                {'title': 'что-то еще', 'url_name': '#'},]
                                           },
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
