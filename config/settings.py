"""
Django settings for the "Code & Forge" (Digital Atelier) project.

Security-first configuration:
- Secrets loaded from environment variables (never hard-coded).
- CSRF protection enforced everywhere (including AJAX).
- Rate limiting enabled via django-ratelimit on the request-a-service view.
- Admin path is not the default "/admin/" and is configurable via env var.
- Secure cookies, HSTS, XSS filtering, and clickjacking protection.
- Django's ORM is used exclusively (no raw SQL) -> protects against SQL Injection.
- Auto-escaping templates (Django default) + bleach sanitization on free-text
  input -> protects against stored/reflected XSS.
"""

import os
from pathlib import Path
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# CORE / SECRETS
# ---------------------------------------------------------------------------
SECRET_KEY = config("DJANGO_SECRET_KEY")  # MUST be set in the environment / .env
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config(
    "DJANGO_ALLOWED_HOSTS",
    default="127.0.0.1,localhost",
    cast=Csv(),
)

# Randomized / secret admin URL path, e.g. "atelier-command-x92f/"
# Set this in your .env — never leave the default admin path in production.
ADMIN_URL_PATH = config("DJANGO_ADMIN_URL", default="atelier-command-portal/")

# ---------------------------------------------------------------------------
# APPLICATIONS
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_ratelimit",
    "services",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,  # Django auto-escapes all variables by default -> XSS-safe
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# DATABASE
# All access goes through Django's ORM (parameterized queries) -> no raw SQL,
# which removes SQL-injection risk by construction.
# ---------------------------------------------------------------------------
if os.environ.get("DATABASE_URL"):
    # Railway / Render inject this automatically when you attach a Postgres
    # add-on — no need to fill DB_* vars by hand in that case.
    DATABASES = {
        "default": dj_database_url.config(
            default=os.environ["DATABASE_URL"],
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": config("DB_ENGINE", default="django.db.backends.sqlite3"),
            "NAME": config("DB_NAME", default=BASE_DIR / "db.sqlite3"),
            "USER": config("DB_USER", default=""),
            "PASSWORD": config("DB_PASSWORD", default=""),
            "HOST": config("DB_HOST", default=""),
            "PORT": config("DB_PORT", default=""),
        }
    }

# ---------------------------------------------------------------------------
# PASSWORD VALIDATION (protects the admin account)
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# INTERNATIONALIZATION
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "ar"
TIME_ZONE = "Asia/Riyadh"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# STATIC FILES
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# SECURITY HEADERS & COOKIES
# ---------------------------------------------------------------------------
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Strict"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
SESSION_COOKIE_AGE = 60 * 30  # 30 minutes admin session timeout

# Trust Railway's proxy header so Django knows the original request was HTTPS
# (Railway terminates SSL and forwards plain HTTP internally, which otherwise
# causes an infinite redirect loop with SECURE_SSL_REDIRECT).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Only force HTTPS-only cookies / redirects when NOT in local DEBUG mode.
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="https://codeforge.example.com",
    cast=Csv(),
)

# ---------------------------------------------------------------------------
# RATE LIMITING (django-ratelimit) — applied in services/views.py
# Blocks spam / automated flooding of the service-request form.
# ---------------------------------------------------------------------------
RATELIMIT_ENABLE = True
RATELIMIT_VIEW = "services.views.ratelimited_error"

# ---------------------------------------------------------------------------
# LOGGING — capture security-relevant events (e.g. blocked/rate-limited requests)
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django.security": {"handlers": ["console"], "level": "WARNING"},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "services": {"handlers": ["console"], "level": "INFO"},
    },
}

# ---------------------------------------------------------------------------
# EMAIL — used to notify the admin instantly of a new service request
# ---------------------------------------------------------------------------
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
ADMIN_NOTIFICATION_EMAIL = config("ADMIN_NOTIFICATION_EMAIL", default="")

FACEBOOK_PAGE_URL = "https://www.facebook.com/share/18ie8XWUJa/"
