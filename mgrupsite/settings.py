from pathlib import Path
from environs import Env

BASE_DIR = Path(__file__).resolve().parent.parent
env = Env()
env.read_env()

SECRET_KEY=env('SECRET_KEY')
DEBUG = False

# ALLOWED_HOSTS = [] # для разработки
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=['mgroup-vvlxvt.amvera.io', 'localhost'])



SITE_ID = 1
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    # 'django_extensions',
    # 'debug_toolbar',
    'ckeditor',
    'taggit',
    'taggit_labels',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.postgres',
    'bootstrap5',
    'job.apps.JobConfig',
    'tgbot',
]

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

ROOT_URLCONF = 'mgrupsite.urls'


CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://127.0.0.1:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': env('REDIS_PASSWORD', default=''),
        },
        'TIMEOUT': 300,
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR/'templates',],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'job.context_processors.menu_context',
            ],
        },
    },
]
WSGI_APPLICATION = 'mgrupsite.wsgi.application'

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

INTERNAL_IPS = env.list("INTERNAL_IPS", default=["127.0.0.1"])

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

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


STATIC_URL = '/static/'

# Правильная конкатенация пути с использованием Pathlib
STATICFILES_DIRS = [BASE_DIR / 'static']

# Место, куда будут собраны статические файлы при выполнении команды `collectstatic`
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
}


MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR/'media'

THUMBNAIL_ALIASES = {
    '': {
        'admin_thumb': {'size': (100, 100), 'crop': True},
    },
}


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# EMAIL_HOST = 'smtp.yandex.ru'
# EMAIL_POR
# EMAIL_HOST_USER = config('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
# EMAIL_USE_SSL = True
#
#
# DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
# SERVER_EMAIL = EMAIL_HOST_USER
# EMAIL_ADMIN = EMAIL_HOST_USER

# TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')
TELEGRAM_BOT_TOKEN = env('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = env('TELEGRAM_CHAT_ID')
# WEBHOOK_HOST = 'https://b14c-94-43-154-7.ngrok-free.app'
WEBHOOK_HOST = 'https://mgroup-vvlxvt.amvera.io'
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'
# NGROK_TOKEN = config('NGROK_TOKEN')
# TG_SERVER_HOST = "127.0.0.1"
TG_SERVER_HOST = "0.0.0.0"
# TG_SERVER_PORT = 8001   # for ngrok
TG_SERVER_PORT = 80
# GOOGLE_MAPS_API_KEY = config('GOOGLE_MAPS_API_KEY')
GOOGLE_MAPS_API_KEY = env('GOOGLE_MAPS_API_KEY')


# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_HOST_USER = config('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
# EMAIL_POST = 587
# EMAIL_USE_TLS = True
# EMAIL_USE_SSL = False
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'