# config/settings/prod.py
from .base import *
import os

if os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes"):
    raise RuntimeError("DEBUG must be False in production!")

DEBUG = False

ALLOWED_HOSTS = ["mgroup-vvlxvt.amvera.io"]
CSRF_TRUSTED_ORIGINS = ["https://mgroup-vvlxvt.amvera.io"]

# ================== БАЗА ДАННЫХ (REMOTE POSTGRES) ==================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("PROD_DB_NAME"),
        "USER": env("PROD_DB_USER"),
        "PASSWORD": env("PROD_DB_PASSWORD"),
        "HOST": env("PROD_DB_HOST"),
        "PORT": env("PROD_DB_PORT", default="5432"),
        "ATOMIC_REQUESTS": True,
    }
}

# ================== MEDIA (S3 / YANDEX CLOUD) ==================
MEDIA_URL = "https://storage.yandexcloud.net/mgroup/"

INSTALLED_APPS += ["storages"]

STATIC_ROOT = "/data/static"

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

AWS_S3_ENDPOINT_URL = "https://storage.yandexcloud.net"
AWS_ACCESS_KEY_ID = env("YANDEX_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("YANDEX_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = "mgroup"

AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None

# ================== TELEGRAM ==================
WEBHOOK_HOST = "https://mgroup-vvlxvt.amvera.io"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

TG_SERVER_HOST = "0.0.0.0"
TG_SERVER_PORT = 80
