import hashlib
import hmac
import logging
import time
import urllib
from itertools import zip_longest

import requests
from django.conf import settings
from django.core.exceptions import PermissionDenied

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


bot_token = settings.TELEGRAM_BOT_TOKEN
external_request_timeout = settings.EXTERNAL_REQUEST_TIMEOUT


class ExternalServiceUnavailable(Exception):
    pass


def verify_telegram_auth(data):
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    auth_data = urllib.parse.parse_qs(data, keep_blank_values=True)
    auth_data = {k: v[0] for k, v in auth_data.items()}
    hash_check = auth_data.pop("hash", None)
    if not hash_check:
        return False
    check_string = "\n".join(f"{k}={auth_data[k]}" for k in sorted(auth_data.keys()))
    calculated_hash = hmac.new(
        secret_key, check_string.encode(), hashlib.sha256
    ).hexdigest()
    auth_date = int(auth_data.get("auth_date", 0))
    if time.time() - auth_date > 86400:
        logger.warning("Telegram authentication data has expired")
        return False

    is_valid = hmac.compare_digest(calculated_hash, hash_check)
    if not is_valid:
        logger.warning("Telegram authentication hash is invalid")
    return is_valid


logger = logging.getLogger(__name__)


def send_telegram_message(question):
    """
    Отправляет сообщение или фото в Telegram на основе экземпляра UserQuestion.

    :param question: экземпляр модели UserQuestion
    :return: bool (успех/неудача)
    """
    user = question.user
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    telegram_url_photo = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

    # Получаем имя пользователя или ID
    user_label = (
        f"@{user.username}"
        if user.username
        else f"User ID: <code>{user.telegram_id}</code>"
    )
    caption = f"{question.question_text}\n\nот пользователя {user_label}"

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
