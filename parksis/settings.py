import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("APP_DEBUG", "False") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")
INTERNAL_IPS = os.environ.get("INTERNAL_IPS", "").split(",")

# Application definition

INSTALLED_APPS = [
    "admin_interface",
    "colorfield",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "rest_framework",
    "rest_framework_gis",
    "django_htmx",
    "django_filters",
    "mathfilters",
    "ortak.apps.OrtakConfig",
    "parkbahce.apps.ParkbahceConfig",
    "istakip.apps.IstakipConfig",
]

X_FRAME_OPTIONS = "SAMEORIGIN"
SILENCED_SYSTEM_CHECKS = ["security.W019"]


MIDDLEWARE = [
    "django_htmx.middleware.HtmxMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "parksis.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "istakip.choices.global_choices_context",
            ],
        },
    },
]

WSGI_APPLICATION = "parksis.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("DB_NAME", "cbsmodel"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}


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

LANGUAGE_CODE = "tr"

TIME_ZONE = "Europe/Istanbul"

USE_I18N = True

USE_TZ = True


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Authentication Settings
LOGIN_URL = "/hesap/giris/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/hesap/giris/"

# Session Settings
SESSION_COOKIE_AGE = 86400 * 7  # 7 gün
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

SRID = 5256

# Default Map Center Coordinates
DEFAULT_MAP_LATITUDE = 39.7480
DEFAULT_MAP_LONGITUDE = 37.0145
DEFAULT_MAP_ZOOM = 13

DISTANCE_PRECISION = 100
if DEBUG:
    DISTANCE_PRECISION = 500  # metre

# Cache ayarları
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache_table",
        "TIMEOUT": 60 * 15,  # 15 dakika
    }
}

# MEDIA_URL = "/media/"
# MEDIA_ROOT = BASE_DIR / "media"
USE_MINIO = os.getenv("USE_MINIO", "False").lower() == "true"


if USE_MINIO:
    # MinIO Settings
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "10.0.0.70:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", os.getenv("AWS_ACCESS_KEY_ID"))
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", os.getenv("AWS_SECRET_ACCESS_KEY"))
    MINIO_BUCKET_NAME = os.getenv(
        "MINIO_BUCKET_NAME", os.getenv("AWS_STORAGE_BUCKET_NAME", "parkbahce")
    )
    MINIO_USE_HTTPS = os.getenv("MINIO_USE_HTTPS", "False").lower() == "true"
    MINIO_CUSTOM_DOMAIN = os.getenv(
        "MINIO_CUSTOM_DOMAIN",
        os.getenv("AWS_S3_CUSTOM_DOMAIN", "parkbahce.sivas.bel.tr"),
    )

    # Static ve Media klasör ayarları
    MINIO_STATIC_FILES_BUCKET = MINIO_BUCKET_NAME
    MINIO_MEDIA_FILES_BUCKET = MINIO_BUCKET_NAME
    MINIO_STATIC_LOCATION = os.getenv("MINIO_STATIC_LOCATION", "static")
    MINIO_MEDIA_LOCATION = os.getenv(
        "MINIO_MEDIA_LOCATION", "media"
    )  # Django 4.2+ Storage System Configuration
    STORAGES = {
        "default": {
            "BACKEND": "parksis.storage_backends.MinIOMediaStorage",
        },
        "staticfiles": {
            "BACKEND": "parksis.storage_backends.MinIOStaticStorage",
        },
    }

    # Legacy support (Django < 4.2 için)
    DEFAULT_FILE_STORAGE = "parksis.storage_backends.MinIOMediaStorage"
    STATICFILES_STORAGE = "parksis.storage_backends.MinIOStaticStorage"

    # Static ve Media URL'leri
    protocol = "https" if MINIO_USE_HTTPS else "http"
    STATIC_URL = f"{protocol}://{MINIO_CUSTOM_DOMAIN}/{MINIO_STATIC_LOCATION}/"
    MEDIA_URL = f"{protocol}://{MINIO_CUSTOM_DOMAIN}/{MINIO_MEDIA_LOCATION}/"

    # STATIC_ROOT collectstatic için gerekli (geçici klasör)
    STATIC_ROOT = BASE_DIR / "static"

    print(f"✅ MinIO Storage aktif: {protocol}://{MINIO_ENDPOINT}")
    print(f"   📦 Bucket: {MINIO_BUCKET_NAME}")
    print(f"   🌐 Domain: {MINIO_CUSTOM_DOMAIN}")
    print(f"   📁 Static: {STATIC_URL}")
    print(f"   📷 Media: {MEDIA_URL}")
else:
    # Local storage (development)
    STATIC_URL = "/static/"
    # STATIC_ROOT = BASE_DIR / "static"
    STATICFILES_DIRS = [BASE_DIR / "static"]
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"
    print("📁 Local storage aktif")
