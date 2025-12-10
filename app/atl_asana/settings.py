import os
from pathlib import Path

from asana.constance_settings import CONSTANCE_CONFIG as ASANA_CONSTANCE_CONFIG
from asana.constance_settings import CONSTANCE_CONFIG_FIELDSETS as ASANA_FIELDSETS
from creative_quality.constance_settings import CONSTANCE_CONFIG as CREATIVE_ESTIMATE_CONSTANCE_CONFIG
from creative_quality.constance_settings import CONSTANCE_CONFIG_FIELDSETS as CREATIVE_ESTIMATE_FIELDSETS
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR.parent / ".env")
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
ASANA_HOOK_SECRET = os.environ["ASANA_HOOK_SECRET"]
DOMAIN_MESSAGE_API_KEY = os.environ["DOMAIN_MESSAGE_API_KEY"]
ASANA_API_KEY = os.environ["ASANA_API_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "83.222.20.96",
    "37.1.208.252",
    "atl-asana.vim-store.ru",
]

CSRF_TRUSTED_ORIGINS = [
    "http://83.222.20.96",
    "http://atl-asana.vim-store.ru",
    "https://atl-asana.vim-store.ru",
    "http://atl-asana.vim-store.ru:81",
    "https://atl-asana.vim-store.ru:81",
]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_extensions",
    "django_celery_results",
    "django_celery_beat",
    'constance',
    # apps
    "vga_lands.apps.VgaLandsConfig",
    "comment_notifier.apps.CommentNotifierConfig",
    "asana.apps.AsanaConfig",
    "webhook_pinger.apps.WebhookPingerConfig",
    "message_sender.apps.MessageSenderConfig",
    "creative_quality.apps.CreativeQualityConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "atl_asana.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "atl_asana.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     },
# }
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ["POSTGRES_HOST"],
        "PORT": "5432",
    },
}


REDIS_HOST = os.environ["REDIS_HOST"]
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:6379/0"
CELERY_RESULT_BACKEND = "django-db"
CELERY_TASK_TRACK_STARTED = True
CELERY_RESULT_EXTENDED = True


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Minsk"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"

STATIC_ROOT = os.path.join(BASE_DIR, "static")

STATICFILES_DIRS = [
    BASE_DIR / "staticfiles",
]


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'

CONSTANCE_ADDITIONAL_FIELDS = {
    "country_select": (
        "django.forms.ChoiceField",
        {
            "widget": "django.forms.Select",
            "choices": (("CA", "CANADA"), ("US", "USA")),
        },
    ),
}


CONSTANCE_CONFIG = {
    "DEFAULT_COUNTRY": (
        "US",
        "Страна по умолчанию",
        "country_select",
    ),
    "ENABLE_SMS_SENDING": (
        True,
        "Включить отправку СМС",
        bool,
    ),
    **ASANA_CONSTANCE_CONFIG,
    **CREATIVE_ESTIMATE_CONSTANCE_CONFIG,

}


CONSTANCE_CONFIG_FIELDSETS = {
    "Examples": (
        "ENABLE_SMS_SENDING",
        "DEFAULT_COUNTRY",
    ),
    **ASANA_FIELDSETS,
    **CREATIVE_ESTIMATE_FIELDSETS,
}
