"""
Django settings for the Slack clone backend.

12-factor: everything environment-specific is read from env vars (via
django-environ) so the same code/image runs in dev, CI, and production. Sections
are labeled with the module that introduces them.
"""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
# Load .env if present (local dev). In containers/k8s, real env vars win.
environ.Env.read_env(BASE_DIR / ".env")

# ── Core ───────────────────────────────────────────────────────────────────────
SECRET_KEY = env("SECRET_KEY", default="dev-only-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "daphne",                       # ASGI server; must precede staticfiles (Module 05)
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",      # Module 11 — full-text search
    # Third-party (enabled as modules introduce them)
    "rest_framework",               # Module 03/04
    "rest_framework_simplejwt.token_blacklist",  # Module 03 — refresh rotation
    "drf_spectacular",              # Module 04
    "django_filters",               # Module 04
    "channels",                     # Module 05
    "django_celery_beat",           # Module 07
    # Local apps
    "accounts",                     # Module 02 — custom User
    "workspaces",                   # Module 02
    "chat",                         # Module 02
    "notifications",                # Module 07
    "webhooks",                     # Module 08
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # static files (Module 12)
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"   # Module 05 — Channels routes through ASGI

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

# ── Database (Module 02) ───────────────────────────────────────────────────────
DATABASES = {"default": env.db("DATABASE_URL", default="postgres://slack:slack@localhost:5432/slack")}

# ── Custom user (Module 02) ────────────────────────────────────────────────────
# Set BEFORE the first migration — changing it later is very painful.
AUTH_USER_MODEL = "accounts.User"

# ── Password / i18n / static ───────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Redis (Modules 05/06/07) ───────────────────────────────────────────────────
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# ── REST framework + SimpleJWT (Module 03/04) ──────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.CursorPagination",
    "PAGE_SIZE": 30,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {"user": "1000/hour", "anon": "30/hour"},
}

SPECTACULAR_SETTINGS = {"TITLE": "Slack Clone API", "VERSION": "0.1.0"}

from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ── Channel layer (Module 05) ──────────────────────────────────────────────────
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}

# ── Celery (Module 07) ─────────────────────────────────────────────────────────
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
# In tests we run tasks inline (no broker/worker needed).
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    "daily-digest": {
        "task": "notifications.tasks.send_daily_digest",
        "schedule": crontab(hour=8, minute=0),   # 08:00 UTC every day
    },
}

# ── Email (Module 07) ──────────────────────────────────────────────────────────
# Defaults to SMTP (MailHog in dev); override to console/locmem in tests/CI.
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=1025)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@slackclone.local")

# ── Object storage (Module 11) ─────────────────────────────────────────────────
S3_ENDPOINT_URL = env("S3_ENDPOINT_URL", default="http://localhost:9000")
S3_ACCESS_KEY = env("S3_ACCESS_KEY", default="minioadmin")
S3_SECRET_KEY = env("S3_SECRET_KEY", default="minioadmin")
S3_BUCKET = env("S3_BUCKET", default="slack-uploads")

# ── CORS/CSRF for the Next.js frontend (Module 09) ─────────────────────────────
FRONTEND_ORIGIN = env("FRONTEND_ORIGIN", default="http://localhost:3000")
CSRF_TRUSTED_ORIGINS = [FRONTEND_ORIGIN]
