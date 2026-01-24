# config/settings/dev.py
from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*", "127.0.0.1", "localhost"]

# ================== БАЗА ДАННЫХ (LOCAL) ==================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DEV_DB_NAME"),
        "USER": env("DEV_DB_USER"),
        "PASSWORD": env("DEV_DB_PASSWORD"),
        "HOST": env("DEV_DB_HOST", default="localhost"),
        "PORT": env("DEV_DB_PORT", default="5432"),
        "ATOMIC_REQUESTS": True,
    }
}

# ================== MEDIA (LOCAL FILESYSTEM) ==================
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": MEDIA_ROOT},
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ================== TELEGRAM ==================
TONNEL_DOMAIN = "https://2124cd0d2925.ngrok-free.app"
CSRF_TRUSTED_ORIGINS = [TONNEL_DOMAIN]

WEBHOOK_HOST = TONNEL_DOMAIN
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

TG_SERVER_HOST = "127.0.0.1"
TG_SERVER_PORT = 8001
