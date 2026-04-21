from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-secret-key-change-me-please-1234567890")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "apps.core.mongo_app_configs.MongoAdminConfig",
    "apps.core.mongo_app_configs.MongoAuthConfig",
    "apps.core.mongo_app_configs.MongoContentTypesConfig",
    "apps.core.mongo_app_configs.MongoSessionsConfig",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "apps.core",
    "apps.tecnicos",
    "apps.clientes",
    "apps.cuentas",
    "apps.inventario",
    "apps.pedidos",
    "apps.dashboard",
    "apps.recomendaciones",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017").strip()
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "sistema_titulacion").strip()

DATABASES = {
    "default": {
        "ENGINE": "django_mongodb_backend",
        "NAME": MONGODB_DB_NAME,
        "HOST": MONGODB_URI,
        "OPTIONS": {
            "serverSelectionTimeoutMS": int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "3000")),
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-pe"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django_mongodb_backend.fields.ObjectIdAutoField"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": [
        "apps.core.renderers.MongoJSONRenderer",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Backend Simplificado OT",
    "DESCRIPTION": "API simple para tecnicos, clientes, cuentas y pedidos con recomendacion.",
    "VERSION": "1.0.0",
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:4010",
    "http://127.0.0.1:4010",
]

cors_extra_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
if cors_extra_origins:
    CORS_ALLOWED_ORIGINS.extend([origin.strip() for origin in cors_extra_origins.split(",") if origin.strip()])
