"""
Django settings for the अपना घर वृद्ध आश्रम project.

Security hardening pass: CSRF/XSS audited, per-IP rate limiting added on
/admin/login.html and /contact/submit/, production security settings added
below (SECURE_SSL_REDIRECT, HSTS, secure cookies, etc) — all OFF by default
via env vars so local dev over plain HTTP keeps working unchanged. Flip them
on in .env only once this is actually deployed behind HTTPS.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Core / security
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-CHANGE-ME")
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if h.strip()
]

# ---------------------------------------------------------------------------
# Production security settings — every one of these defaults to "off"/dev-
# safe so local development over plain HTTP on 127.0.0.1 is unaffected.
# Set the corresponding env var in .env only once this is deployed behind
# real HTTPS — turning SECURE_SSL_REDIRECT or the *_COOKIE_SECURE flags on
# over plain HTTP will lock you out (redirect loops / cookies never sent).
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "False") == "True"
SESSION_COOKIE_SECURE = os.environ.get("DJANGO_SESSION_COOKIE_SECURE", "False") == "True"
CSRF_COOKIE_SECURE = os.environ.get("DJANGO_CSRF_COOKIE_SECURE", "False") == "True"
# Hosts like PythonAnywhere terminate HTTPS at a proxy and forward plain HTTP
# to Django; this tells Django the original request was HTTPS. Only enable it
# (DJANGO_BEHIND_PROXY=True) on such a host.
if os.environ.get("DJANGO_BEHIND_PROXY", "False") == "True":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "0"))
# Safe to leave on in dev too — it's just a response header, never breaks
# anything locally, and it's exactly what stops an uploaded file (SiteImage)
# from ever being MIME-sniffed into something executable by the browser.
SECURE_CONTENT_TYPE_NOSNIFF = os.environ.get("DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", "True") == "True"
X_FRAME_OPTIONS = os.environ.get("DJANGO_X_FRAME_OPTIONS", "DENY")
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]

# ---------------------------------------------------------------------------
# Cache — backs the per-IP rate limiting in core/ratelimit.py (admin login,
# contact form). LocMemCache is per-process: fine for a single `runserver`
# / single-worker deployment, but each worker gets its own counters under
# multiple Gunicorn workers, so the effective limit multiplies by worker
# count. Swap to Redis/memcached there if that matters at your scale.
# ---------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "clothingbank",
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
        "DIRS": [BASE_DIR / "core" / "templates"],
        "APP_DIRS": True,
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
# Database — MySQL (falls back to sqlite only if you explicitly set
# USE_SQLITE=True in .env, handy for a very first smoke test)
# ---------------------------------------------------------------------------
if os.environ.get("USE_SQLITE") == "True":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DB_NAME", "apnaghar_db"),
            "USER": os.environ.get("DB_USER", "apnaghar_user"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DB_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",  # required for Hindi/Devanagari text
            },
        }
    }

# ---------------------------------------------------------------------------
# Password validation (used once real accounts exist — Milestone 2)
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & media files
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "core" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"  # populated by collectstatic for production
STORAGES = {
    # Overriding STORAGES replaces Django's defaults wholesale, so "default"
    # (used by FileField/ImageField, i.e. SiteImage uploads) must be listed
    # explicitly too, not just "staticfiles".
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"  # SiteImage uploads (Site Content, superuser-only) live here
# MEDIA_ROOT is a plain sibling directory of STATIC_ROOT, not nested inside
# any app/code directory — nothing here is ever imported or executed by
# Django itself. Two more guarantees on top of that, enforced in
# clothingbank/views.py's upload view (api_site_image_upload):
#   1. Every uploaded file is re-saved under a name WE generate
#      (uuid4().hex + an extension), and that extension is chosen from a
#      fixed map keyed on Pillow's *verified* decoded format — never from
#      the client's filename or Content-Type header. So nothing with a
#      .php/.html/.svg-style extension can ever land in MEDIA_ROOT.
#   2. SECURE_CONTENT_TYPE_NOSNIFF (below) sends X-Content-Type-Options:
#      nosniff, so even if a browser wanted to re-interpret a served
#      image/jpeg as something executable, it's told not to.
# In production, MEDIA_ROOT is typically served directly by Nginx rather
# than Django — when you set that up, give /media/ its own `location` block
# with NO fastcgi/php/CGI handler attached (Nginx only ever executes a file
# if a location block explicitly says to; it doesn't auto-execute based on
# extension the way old Apache+mod_php setups could). That Nginx config
# lives outside this repo, so it's not something this settings file can
# enforce — treat this comment as the checklist item for whoever writes it.
#
# Uploaded files must never be saved executable on disk either, regardless
# of the server's umask — 0o644 = rw-r--r--, no execute bit for anyone.
FILE_UPLOAD_PERMISSIONS = 0o644

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Where Django's login_required / LoginView send users
LOGIN_URL = "admin_login"
LOGIN_REDIRECT_URL = "admin_dashboard"
LOGOUT_REDIRECT_URL = "admin_login"
