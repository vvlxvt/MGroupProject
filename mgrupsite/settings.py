from pathlib import Path
from environs import Env

# === Базовые переменные ===
BASE_DIR = Path(__file__).resolve().parent.parent
env = Env()
env.read_env()

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=['mgroup-vvlxvt.amvera.io', 'localhost'])
CSRF_TRUSTED_ORIGINS = ['https://mgroup-vvlxvt.amvera.io']
SITE_ID = 1

# === Установленные приложения ===
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',

    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.postgres',

    'ckeditor',
    'taggit',
    'taggit_labels',
    'bootstrap5',
    'storages',

    'job.apps.JobConfig',
    'tgbot',

    # 'debug_toolbar',
    # 'django_extensions',
]

# === Middleware ===
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# === URL и WSGI ===
ROOT_URLCONF = 'mgrupsite.urls'
WSGI_APPLICATION = 'mgrupsite.wsgi.application'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
# === Шаблоны ===
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'job.context_processors.menu_context',
            ],
        },
    },
]

#=== Логгирование ===
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}


# === База данных ===
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
        'ATOMIC_REQUESTS': True,
    },
}

# === Локализация ===
LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# === Статика и медиа ===
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = "/data/static"

# MEDIA_URL = "/media/"
MEDIA_URL = "https://storage.yandexcloud.net/mgroup/"
# MEDIA_ROOT = "/data/media"

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
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
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# === Внутренние IP ===
INTERNAL_IPS = env.list("INTERNAL_IPS", default=["127.0.0.1"])

# === Telegram и внешние сервисы ===
TELEGRAM_BOT_TOKEN = env('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = env('TELEGRAM_CHAT_ID')

WEBHOOK_HOST = 'https://mgroup-vvlxvt.amvera.io'
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

TG_SERVER_HOST = "0.0.0.0"
TG_SERVER_PORT = 80

GOOGLE_MAPS_API_KEY = env('GOOGLE_MAPS_API_KEY')

# === Прочее ===
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

THUMBNAIL_ALIASES = {
    '': {
        'admin_thumb': {'size': (100, 100), 'crop': True},
    },
}


AWS_S3_ENDPOINT_URL = 'https://storage.yandexcloud.net'
AWS_ACCESS_KEY_ID = env('YANDEX_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('YANDEX_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = 'mgroup'

AWS_QUERYSTRING_AUTH = False  # отключить подписи в URL (для прямых ссылок)
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None  # отключить управление ACL

# === Email (закомментирован, включайте при необходимости) ===
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_HOST_USER = env('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
# SERVER_EMAIL = EMAIL_HOST_USER
# EMAIL_ADMIN = EMAIL_HOST_USER
