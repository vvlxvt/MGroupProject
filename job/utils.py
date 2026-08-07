import logging
from itertools import zip_longest

import requests
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.html import escape

class DataMixin:
    paginate_by = 6
    title_page = None
    extra_context = {}

    def __init__(self):
        if self.title_page:
            self.extra_context["title"] = self.title_page


folder = "static/job/images/advantages/"

advantages = {
    "color": {
        "title": "Выбор цвета",
        "content": "Предоставляем полный спектр цветов для вышего объекта",
        "icon": f"{folder}palette.png",
    },
    "guarantee": {
        "title": "Гарантия на работы",
        "content": "На все выполненные работы мы даем официальную гарантию",
        "icon": f"{folder}guarantee.png",
    },
    "price": {
        "title": "Цена известна заранее",
        "content": "Мы составляем план и детальную смету. Полный документооборот",
        "icon": f"{folder}low-price.png",
    },
    "design": {
        "title": "Дизайн проект",
        "content": "Может быть полностью ваш или доработан после консультации наших специалистов",
        "icon": f"{folder}planning.png",
    },
    "quality": {
        "title": "Качественные материалы",
        "content": "Работаем с лучшими, проверенными производителями оборудования и материалов",
        "icon": f"{folder}color.png",
    },
    "specialist": {
        "title": "Специалисты своего дела",
        "content": "Мы за разделение труда. Над каждым проектом работают специалисты узкого профиля",
        "icon": f"{folder}worker.png",
    },
}


partners = {
    "Роснефть": "static/job/images/partners/partners-rosneft.png",
    "Красэнерго": "static/job/images/partners/partners-krasenergo.png",
    "Славнефть": "static/job/images/partners/partners-slavneft.png",
    "Леруа-Мерлен": "static/job/images/partners/partners-Leroy-Merli.png",
    "Лента": "static/job/images/partners/partners-lenta.png",
    "КраМЗ": "static/job/images/partners/partners-kramz.jpg",
    "БНГРЭ": "static/job/images/partners/partners-bngre.jpg",
    "РН-Бурение": "static/job/images/partners/partners-rnburenie.png",
}


def chunk_list(lst, size):
    """Разделяет список на группы заданного размера."""
    return list(zip_longest(*[iter(lst)] * size, fillvalue=None))


external_request_timeout = settings.EXTERNAL_REQUEST_TIMEOUT


class ExternalServiceUnavailable(Exception):
    pass


logger = logging.getLogger(__name__)


def send_telegram_message(question):
    """
    Отправляет сообщение или фото в Telegram на основе экземпляра UserQuestion.

    :param question: экземпляр модели UserQuestion
    :return: bool (успех/неудача)
    """
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    telegram_url_photo = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

    sender = question.contact_email or "email не указан"
    caption = (
        f"{escape(question.question_text)}\n\n"
        f"Email для ответа: <code>{escape(sender)}</code>"
    )

    try:
        if question.attached_photo:
            with question.attached_photo.open("rb") as photo_file:
                files = {"photo": photo_file}
                response = requests.post(
                    telegram_url_photo,
                    data={
                        "chat_id": chat_id,
                        "caption": caption,
                        "parse_mode": "HTML",
                    },
                    files=files,
                    timeout=external_request_timeout,
                )
        else:
            response = requests.post(
                telegram_url,
                data={
                    "chat_id": chat_id,
                    "text": caption,
                    "parse_mode": "HTML",
                },
                timeout=external_request_timeout,
            )

        response.raise_for_status()
        return True

    except Exception as exc:
        logger.error(
            "Telegram notification delivery failed",
            extra={
                "question_id": question.pk,
                "error_type": type(exc).__name__,
            },
        )
        return False


def verify_recaptcha(token: str, action: str, min_score: float = 0.5):
    if not token:
        raise PermissionDenied("Missing reCAPTCHA token")

    try:
        response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": settings.RECAPTCHA_SECRET_KEY,
                "response": token,
            },
            timeout=external_request_timeout,
        )
        response.raise_for_status()
        result = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("reCAPTCHA service is unavailable: %s", exc)
        raise ExternalServiceUnavailable from exc

    if not result.get("success"):
        raise PermissionDenied("reCAPTCHA verification failed")

    if result.get("action") != action:
        raise PermissionDenied("Invalid reCAPTCHA action")

    if result.get("score", 0) < min_score:
        raise PermissionDenied("Low reCAPTCHA score")

    if result.get("hostname") not in settings.ALLOWED_RECAPTCHA_HOSTS:
        raise PermissionDenied("Invalid hostname")
