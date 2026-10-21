import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# --------------------------------------------------
# SECURITY
# --------------------------------------------------

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "dev-only-change-this-before-deploying",
)

DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        "localhost,127.0.0.1",
    ).split(",")
    if host.strip()
]


# --------------------------------------------------
# APPLICATIONS
# --------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",

    "rest_framework",
    "corsheaders",
    "channels",

    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",

    "accounts",
    "library",
    "social",
    "clubs",
]


# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

DB_ENGINE = os.getenv(
    "DB_ENGINE",
    "django.db.backends.mysql",
).strip()

if DB_ENGINE == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            # DB_NAME is useful for isolated checks and tests.  When unset,
            # keep the existing local SQLite database path.
            "NAME": os.getenv("DB_NAME") or BASE_DIR / "db.sqlite3",
        }
    }

elif DB_ENGINE == "django.db.backends.mysql":
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": os.getenv("DB_NAME", "follia_library"),
            "USER": os.getenv("DB_USER", "follia_user"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
            },
        }
    }

else:
    raise ValueError(f"Unsupported DB_ENGINE: {DB_ENGINE}")


# --------------------------------------------------
# PASSWORD VALIDATION
# --------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        )
    },
]


# --------------------------------------------------
# INTERNATIONALIZATION
# --------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True


# --------------------------------------------------
# STATIC AND MEDIA FILES
# --------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# R2 credentials stay on the backend.  A custom domain is optional: without
# one, django-storages returns short-lived signed URLs for private bucket
# objects.
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "").strip()
# Preserve compatibility with the existing configuration, which supplies
# CLOUDFLARE_ACCOUNT_ID. Explicit R2_ENDPOINT_URL remains an optional override.
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL", "").strip().rstrip("/")
if not R2_ENDPOINT_URL and CLOUDFLARE_ACCOUNT_ID:
    R2_ENDPOINT_URL = f"https://{CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com"
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "").strip()
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "").strip()
R2_REGION = os.getenv("R2_REGION", "auto").strip() or "auto"
R2_PUBLIC_DOMAIN = os.getenv("R2_PUBLIC_DOMAIN", "").strip().rstrip("/")
if R2_PUBLIC_DOMAIN.startswith(("https://", "http://")):
    R2_PUBLIC_DOMAIN = R2_PUBLIC_DOMAIN.split("://", 1)[1].split("/", 1)[0]
else:
    R2_PUBLIC_DOMAIN = R2_PUBLIC_DOMAIN.split("/", 1)[0]

R2_STORAGE_CONFIGURED = all(
    (
        R2_BUCKET_NAME,
        R2_ENDPOINT_URL,
        R2_ACCESS_KEY_ID,
        R2_SECRET_ACCESS_KEY,
    )
)

if R2_STORAGE_CONFIGURED:
    DEFAULT_MEDIA_STORAGE = "config.storage_backends.R2MediaStorage"
elif DEBUG:
    # Keep local development usable without R2 credentials.
    DEFAULT_MEDIA_STORAGE = "django.core.files.storage.FileSystemStorage"
else:
    # Production must not silently put new uploads on ephemeral local disk.
    DEFAULT_MEDIA_STORAGE = "config.storage_backends.R2MediaStorage"

STORAGES = {
    "default": {
        "BACKEND": DEFAULT_MEDIA_STORAGE,
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --------------------------------------------------
# DJANGO ALLAUTH: EMAIL AUTHENTICATION
# --------------------------------------------------

SITE_ID = 1

LOGIN_URL = "/accounts/login/"

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
) or "http://localhost:5173"
FRONTEND_URL = FRONTEND_URL.rstrip("/")
FOLLIA_PUBLIC_URL = (os.getenv("FOLLIA_PUBLIC_URL", "").strip() or FRONTEND_URL).rstrip("/")
FFMPEG_BINARY = os.getenv("FFMPEG_BINARY", "ffmpeg").strip() or "ffmpeg"

LOGIN_REDIRECT_URL = FRONTEND_URL + "/"

# Email verification remains available, but does not block authentication.
ACCOUNT_EMAIL_VERIFICATION = "none"

ACCOUNT_LOGIN_METHODS = {"email"}

ACCOUNT_SIGNUP_FIELDS = [
    "email*",
    "password1*",
    "password2*",
]

ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"

ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = (
    FRONTEND_URL + "/login?verified=1"
)

ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = (
    FRONTEND_URL + "/"
)

ACCOUNT_ADAPTER = "accounts.adapters.FolliaAccountAdapter"
SOCIALACCOUNT_ADAPTER = "accounts.adapters.FolliaSocialAccountAdapter"
SOCIALACCOUNT_ONLY = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"


# --------------------------------------------------
# GOOGLE SIGN-IN
# --------------------------------------------------

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APPS": [
            {
                "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
                "secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
                "key": "",
            }
        ],
        "SCOPE": ["profile", "email"],
        # Google's verified email can safely reconnect an existing local
        # account that predates Google sign-in. Persist the connection so
        # later sign-ins go straight through the normal OAuth callback.
        "EMAIL_AUTHENTICATION": True,
        "EMAIL_AUTHENTICATION_AUTO_CONNECT": True,
        "AUTH_PARAMS": {
            "access_type": "online",
            "prompt": "select_account",
        },
    }
}

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "").strip()
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "").strip()
VAPID_SUBJECT = os.getenv("VAPID_SUBJECT", "").strip()


# --------------------------------------------------
# EMAIL: BREVO SMTP
# --------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Brevo SMTP server settings
EMAIL_HOST = os.getenv(
    "EMAIL_HOST",
    "smtp-relay.brevo.com",
)

EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))

# These must be your Brevo SMTP credentials,
# not your Brevo API key.
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")

EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "1") == "1"
EMAIL_USE_SSL = False
EMAIL_TIMEOUT = 20

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    "Follia Library <noreply@example.com>",
)


# --------------------------------------------------
# FRONTEND, CORS AND CSRF
# --------------------------------------------------

CORS_ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in (
        os.getenv("CORS_ALLOWED_ORIGINS")
        or
        (
            "http://localhost:5173,"
            "http://127.0.0.1:5173,"
            "http://localhost:5174,"
            "http://127.0.0.1:5174"
        )
    ).split(",")
    if origin.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in (os.getenv("CSRF_TRUSTED_ORIGINS") or ",".join(CORS_ALLOWED_ORIGINS)).split(",")
    if origin.strip()
]

CORS_ALLOW_CREDENTIALS = True

SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE") or ("None" if not DEBUG else "Lax")
CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE") or SESSION_COOKIE_SAMESITE
SESSION_COOKIE_SECURE = not DEBUG or SESSION_COOKIE_SAMESITE == "None"
CSRF_COOKIE_SECURE = not DEBUG or CSRF_COOKIE_SAMESITE == "None"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False


# --------------------------------------------------
# DJANGO REST FRAMEWORK
# --------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": (
        "rest_framework.pagination.PageNumberPagination"
    ),
    "PAGE_SIZE": 30,
}


# --------------------------------------------------
# DJANGO CHANNELS
# --------------------------------------------------

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}


# --------------------------------------------------
# PASSWORD RESET
# --------------------------------------------------

PASSWORD_RESET_TIMEOUT = 3600
