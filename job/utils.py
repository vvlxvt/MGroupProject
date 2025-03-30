from itertools import zip_longest
from random import random

class DataMixin:
    paginate_by = 3
    title_page = None
    extra_context = {}

    def __init__(self):
        if self.title_page:
            self.extra_context['title'] = self.title_page


import random
def generate_verification_code():
    code = random.randint(1000, 9999)
    return code


import jwt
import datetime

SECRET_KEY = "xyz"

def generate_code(user):
    payload = {
        "user": user,
        "code": "1424",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")



advantages = {
    "Гарантия на работы": "На все выполненные работы мы даем официальную гарантию",
    "Цена известна заранее": "Она фиксирована. Мы составляем план и детальную смету. Полный документооборот",
    "Дизайн проект": "Может быть полностью ваш или доработан после консультации наших специалистов",
    "Качественные материалы": "Работаем с лучшими, проверенными производителями оборудования и материалов",
    "Специалисты своего дела": "Мы за разделение труда. Над каждым проектом работают специалисты узкого профиля",
    "Выбор цвета": "Предоставляем полный спектр цветов, поможем подобрать оттенок для объекта"
}

partners = {
    'Роснефть': "static/job/images/partners/partners-rosneft.png",
    'Красэнерго': "static/job/images/partners/partners-krasenergo.png",
    'Славнефть': "static/job/images/partners/partners-slavneft.png",
    'Леруа-Мерлен': "static/job/images/partners/partners-Leroy-Merli.png",
    'Лента': "static/job/images/partners/partners-lenta.png",
    'КраМЗ': "static/job/images/partners/partners-kramz.jpg",
    'БНГРЭ': "static/job/images/partners/partners-bngre.jpg",
    'РН-Бурение': "static/job/images/partners/partners-rnburenie.png"
}

def chunk_list(lst, size):
    """Разделяет список на группы заданного размера."""
    return list(zip_longest(*[iter(lst)] * size, fillvalue=None))

