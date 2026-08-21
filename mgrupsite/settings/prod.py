
from .base import *
import os

if os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes"):
    raise RuntimeError("DEBUG must be False in production!")

DEBUG = False

CACHES["default"]["LOCATION"] = env("CACHE_LOCATION", default="/data/cache")

ALLOWED_HOSTS = env.list(
    "APP_HOSTS",
    default=["mgroup-vvlxvt.amvera.io", "xn--c1arkads.xn--p1ai"],
)
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "https://mgroup-vvlxvt.amvera.io",
        "https://xn--c1arkads.xn--p1ai",
    ],
)
CANONICAL_BASE_URL = env(
    "CANONICAL_BASE_URL",
    default="https://mgroup-vvlxvt.amvera.io",
).rstrip("/")

# ================== HTTPS ==================
# TLS terminates at the platform proxy; SECURE_PROXY_SSL_HEADER is configured
# in base.py so Django can recognize the original HTTPS request.
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365

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
    "default": {  # MEDIA на S3
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {  # Локальная статика для WhiteNoise
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        "LOCATION": STATIC_ROOT,
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
WEBHOOK_HOST = env("WEBHOOK_HOST", default=CANONICAL_BASE_URL).rstrip("/")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

TG_SERVER_HOST = "0.0.0.0"
TG_SERVER_PORT = 80

