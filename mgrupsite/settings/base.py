
from pathlib import Path
from environs import Env

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = Env()
env.read_env()

# ================== ОСНОВНОЕ ==================
SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ================== ПРИЛОЖЕНИЯ ==================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",

    "django.contrib.sitemaps",
    "django.contrib.postgres",

    "django_tiptap_editor",
    "taggit",
    "taggit_labels",
    "job.apps.JobConfig",
    "tgbot",
]

# ================== MIDDLEWARE ==================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ================== URL / WSGI ==================
ROOT_URLCONF = "mgrupsite.urls"
WSGI_APPLICATION = "mgrupsite.wsgi.application"

# ================== ШАБЛОНЫ ==================
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

# ================== ЛОКАЛЬ ==================
LANGUAGE_CODE = "ru-RU"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ================== КЭШ ==================
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": BASE_DIR / ".django-cache",
    }
}
MENU_CACHE_TIMEOUT = 60 * 60
CANONICAL_BASE_URL = env("CANONICAL_BASE_URL", default="").rstrip("/")

# ================== СТАТИКА (общая) ==================
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

# ================== БЕЗОПАСНОСТЬ ==================
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ================== ВНЕШНИЕ СЕРВИСЫ ==================
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = env("TELEGRAM_CHAT_ID")
GOOGLE_MAPS_API_KEY = env("GOOGLE_MAPS_API_KEY")
RECAPTCHA_SECRET_KEY = env(
    "RECAPTCHA_SECRET_KEY",
    default=env("RECAPTCHA_PRIVATE_KEY", default=""),
)
RECAPTCHA_SITE_KEY = env(
    "RECAPTCHA_SITE_KEY",
    default=env("RECAPTCHA_PUBLIC_KEY", default=""),
)
ALLOWED_RECAPTCHA_HOSTS = env.list(
    "ALLOWED_RECAPTCHA_HOSTS",
    default=["mgroup-vvlxvt.amvera.io", "xn--c1arkads.xn--p1ai"],
)
EXTERNAL_REQUEST_TIMEOUT = 10
FEEDBACK_RETENTION_DAYS = env.int("FEEDBACK_RETENTION_DAYS", default=30)
YANDEX_METRIKA_ID = env.int("YANDEX_METRIKA_ID", default=111433025)

# Backups use a separate private bucket. Credentials may be isolated from the
# media bucket credentials, but fall back to them for a gradual rollout.
BACKUP_S3_BUCKET = env("BACKUP_S3_BUCKET", default="")
BACKUP_S3_PREFIX = env("BACKUP_S3_PREFIX", default="mgroup-production")
BACKUP_S3_ENDPOINT_URL = env(
    "BACKUP_S3_ENDPOINT_URL", default="https://storage.yandexcloud.net"
)
BACKUP_S3_ACCESS_KEY_ID = env(
    "BACKUP_S3_ACCESS_KEY_ID", default=env("YANDEX_ACCESS_KEY_ID", default="")
)
BACKUP_S3_SECRET_ACCESS_KEY = env(
    "BACKUP_S3_SECRET_ACCESS_KEY",
    default=env("YANDEX_SECRET_ACCESS_KEY", default=""),
)
BACKUP_DATABASE_TIMEOUT_SECONDS = env.int(
    "BACKUP_DATABASE_TIMEOUT_SECONDS", default=1800
)
BACKUP_PGSSLMODE = env("BACKUP_PGSSLMODE", default="prefer")

# ================== ПРОЧЕЕ ==================
INTERNAL_IPS = env.list("INTERNAL_IPS", default=["127.0.0.1"])

THUMBNAIL_ALIASES = {
    "": {"admin_thumb": {"size": (100, 100), "crop": True}},
}
