from random import random


namespace = 'job'

menu = {
    'about': {'title': 'О нас', 'url_name': f'{namespace}:about'},
    'services': {
        'title': 'Услуги',
        'url_name': f'{namespace}:post_list',
        'submenus': [
            {'title': 'Покраска и антикоррозийная обработка поверхностей', 'url_name': f'{namespace}:post_list', 'slug': 'pokraska-i-antikorrozijnaya-obrabotka-poverhnostej'},
            {'title': 'Пескоструйная и гидроструйная обработка поверхности', 'url_name': f'{namespace}:post_list', 'slug': 'peskostrujnaya-i-gidrostrujnaya-obrabotka-poverhnosti'},
            {'title': 'Огнезащитная обработка металла и древесины', 'url_name': f'{namespace}:post_list', 'slug': 'ognezashitnaya-obrabotka-metalla-i-drevesiny'},
            {'title': 'Нанесение жидких теплоизоляционных материалов', 'url_name': f'{namespace}:post_list', 'slug': 'nanesenie-zhidkih-teploizolyacionnyh-materialov'},
            {'title': 'Нанесение гидроизоляционных материалов', 'url_name': f'{namespace}:post_list', 'slug': 'nanesenie-gidroizolyacionnyh-materialov'},
            {'title': 'Нанесение декоративной штукатурки', 'url_name': f'{namespace}:post_list', 'slug': 'nanesenie-dekorativnoj-shtukaturki'},
        ]
    },
    'articles': {'title': 'Статьи', 'url_name': f'{namespace}:article_list'},
    'projects': {'title': 'Проекты', 'url_name': f'{namespace}:projects'},
    'contacts': {'title': 'Контакты', 'url_name': f'{namespace}:contacts'},
}

services = {
    'industrial_painting': {'title': 'Промышленная покраска',
                            'url_name': '#',
                            'submenus': [
                                        {'title': 'Покраска металлоконструкций', 'url_name': 'pokraska-metallokonstrukcij'},
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
                                                {'title': 'Пескоструйная очистка', 'url_name': '#'},
                                                {'title': 'Огнезащита', 'url_name': '#'},
                                                {'title': 'Антикорозийная обработка', 'url_name': '#'}, ],
                                        },
                'insulation_application': {'title': 'Нанесение изоляции',
                                           'url_name': '#',
                                           'submenu': [
                                                {'title': 'Нанесение термоизоляции', 'url_name': '#'},
                                                {'title': 'Что-то еще', 'url_name': '#'},]
                                           },
    }


class DataMixin:
    paginate_by = 3
    title_page = None
    extra_context = {}

    def __init__(self):
        if self.title_page:
            self.extra_context['title'] = self.title_page


from django.core.cache import cache
import random

# def generate_verification_code_with_cache(tg_username):
#     code = random.randint(1000, 9999)
#     cache.set(f'verification_code_{tg_username}', code, timeout=600)  # Срок действия 10 минут
#     return code
#
# def verify_code_with_cache(tg_username, input_code):
#     cached_code = cache.get(f'verification_code_{tg_username}')
#     if not cached_code:
#         return False
#     return True if cached_code == input_code else False
def generate_verification_code():
    code = random.randint(1000, 9999)
    return code