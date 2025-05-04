from itertools import zip_longest
import hashlib
import hmac
import time
import urllib
import requests, json, logging
from django.core.files.base import ContentFile
from django.conf import settings


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
        "content": "На все выполненные работы мы даем официальную гарантию",
        "icon": f"{folder}palette.png",
    },
    "guarantee": {
        "title": "Гарантия на работы",
        "content": "На все выполненные работы мы даем официальную гарантию",
        "icon": f"{folder}guarantee.png",
    },
    "price": {
        "title": "Цена известна заранее",
        "content": "Она фиксирована. Мы составляем план и детальную смету. Полный документооборот",
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
        print("❌ Данные устарели!")
        return False
    else:
        print("✅ Данные актуальны!")
    return calculated_hash == hash_check


def get_user_photo_id(telegram_id):
    """Получает file_id аватара пользователя"""
    url = f"https://api.telegram.org/bot{bot_token}/getUserProfilePhotos"
    params = {"user_id": telegram_id, "limit": 1}

    response = requests.get(url, params=params).json()
    print(json.dumps(response, indent=4, ensure_ascii=False))

    if response["ok"] and response["result"]["total_count"] > 0:
        return response["result"]["photos"][0][-1][
            "file_id"
        ]  # Берём фото максимального размера
    return None


def download_user_photo(file_id):
    """Скачивает фото пользователя с Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/getFile"
    response = requests.get(url, params={"file_id": file_id}).json()

    if response["ok"]:
        file_path = response["result"]["file_path"]
        photo_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        return photo_url  # Это рабочая ссылка на файл!
    return None


def save_user_photo(user):
    """Получает и сохраняет фото пользователя"""
    file_id = get_user_photo_id(user.telegram_id)
    if not file_id:
        print("⚠ Фото отсутствует")
        return

    photo_url = download_user_photo(file_id)
    if not photo_url:
        print("❌ Не удалось получить ссылку на фото")
        return

    try:
        response = requests.get(photo_url, stream=True)
        if response.status_code == 200:
            file_name = f"telegram_photos/{user.telegram_id}.jpg"
            user.photo.save(file_name, ContentFile(response.content), save=True)
            print(f"✅ Фото {file_name} успешно сохранено")
        else:
            print(f"❌ Ошибка загрузки фото: {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Ошибка при запросе к {photo_url}: {e}")


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
                )
        else:
            response = requests.post(
                telegram_url,
                data={
                    "chat_id": chat_id,
                    "text": caption,
                    "parse_mode": "HTML",
                },
            )

        response.raise_for_status()
        return True

    except Exception as e:
        logger.error(f"Ошибка при отправке в Telegram: {e}")
        return False
