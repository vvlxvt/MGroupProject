from pathlib import Path
from decouple import config
from environs import Env

# === Базовые переменные ===
BASE_DIR = Path(__file__).resolve().parent.parent

env = Env()
env.read_env()

SECRET_KEY = config("SECRET_KEY")
DEBUG = True  # На проде: DEBUG = config("DEBUG", cast=bool, default=False)

TONNEL_DOMAIN = "https://tdiebepstu.sharedwithexpose.com"
ALLOWED_HOSTS = ["*", TONNEL_DOMAIN]
CSRF_TRUSTED_ORIGINS = [TONNEL_DOMAIN]
SITE_ID = 1

# === Установленные приложения ===
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",

    "django.contrib.sites",
    "django.contrib.sitemaps",
    "django.contrib.postgres",

    "ckeditor",
    "taggit",
    "taggit_labels",
    "bootstrap5",

    "job.apps.JobConfig",
    "tgbot",

    # "debug_toolbar",
    # "django_extensions",
]

# === Middleware ===
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# === URL и WSGI ===
ROOT_URLCONF = "mgrupsite.urls"
WSGI_APPLICATION = "mgrupsite.wsgi.application"

# === Кэш ===
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://127.0.0.1:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": env("REDIS_PASSWORD", default=""),
        },
        "TIMEOUT": 300,
    }
}

# === Шаблоны ===
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "job.context_processors.menu_context",
                "job.context_processors.canonical_url",
            ],
        },
    },
]

# === База данных ===
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
        "ATOMIC_REQUESTS": True,
    }
}

# === Локализация ===
LANGUAGE_CODE = "ru-RU"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# === Статика и медиа ===
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": BASE_DIR / "media",
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# === Безопасность ===
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# === Telegram и внешние сервисы ===
TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = config("TELEGRAM_CHAT_ID")

WEBHOOK_HOST = TONNEL_DOMAIN
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

NGROK_TOKEN = config("NGROK_TOKEN")
TG_SERVER_HOST = "127.0.0.1"
TG_SERVER_PORT = 8001

GOOGLE_MAPS_API_KEY = config("GOOGLE_MAPS_API_KEY")

# === Прочее ===
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
INTERNAL_IPS = env.list("INTERNAL_IPS", default=["127.0.0.1"])
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

THUMBNAIL_ALIASES = {
    "": {
        "admin_thumb": {"size": (100, 100), "crop": True},
    },
}

# === Email (закомментирован, включайте при необходимости) ===
# EMAIL_HOST = "smtp.gmail.com"
# EMAIL_HOST_USER = config("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
