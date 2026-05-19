"""
Django settings — Настройки проекта EduPlatform KZ

Секреты загружаются из .env файла через python-dotenv.
Никогда не храните пароли и ключи в коде!
"""
from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла (если он существует)
load_dotenv(Path(__file__).resolve().parent.parent / '.env', override=True)

# Корневая папка проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================
# БЕЗОПАСНОСТЬ — КРИТИЧЕСКИ ВАЖНЫЕ НАСТРОЙКИ
# ============================================

# Секретный ключ для криптографических операций Django.
# В production ОБЯЗАТЕЛЬНО задавать через .env файл!
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-change-this-in-production-12345'
)

# Режим отладки. В production ДОЛЖЕН быть False!
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

# Список разрешённых хостов. В production добавить реальный домен.
ALLOWED_HOSTS = os.environ.get(
    'ALLOWED_HOSTS',
    'localhost,127.0.0.1'
).split(',')

# ============================================
# ПРИЛОЖЕНИЯ (Apps)
# ============================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Сторонние библиотеки
    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # Чёрный список токенов (для logout)

    # Наши приложения
    'users',
    'courses',
]

# ============================================
# MIDDLEWARE
# ============================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',     # CORS — должен быть первым!
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ============================================
# БАЗА ДАННЫХ
# ============================================
# SQLite для разработки. Для production используйте PostgreSQL.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ============================================
# КАСТОМНАЯ МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ
# ============================================
AUTH_USER_MODEL = 'users.User'

# Валидация паролей (NIST-совместимые требования)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================
# ЛОКАЛИЗАЦИЯ
# ============================================
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Almaty'
USE_I18N = True
USE_TZ = True

# Статические и медиафайлы
STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# КЭШ — используется для хранения WebAuthn challenge
# ============================================
# В разработке: LocMemCache (в памяти процесса, не шарится между воркерами).
# В production: заменить на Redis:
#   pip install django-redis
#   'BACKEND': 'django_redis.cache.RedisCache'
#   'LOCATION': 'redis://127.0.0.1:6379/1'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'eduplatform-webauthn-cache',
    }
}

# ============================================
# WEBAUTHN / PASSKEY НАСТРОЙКИ
# ============================================
# RP_ID — домен вашего сайта (без порта, без протокола).
# В production: 'eduplatform.kz' или ваш реальный домен.
# ВАЖНО: credential привязан к RP_ID! Если изменить — все ключи сломаются.
WEBAUTHN_RP_ID = os.environ.get('WEBAUTHN_RP_ID', 'localhost')
WEBAUTHN_RP_NAME = os.environ.get('WEBAUTHN_RP_NAME', 'EduPlatform KZ')

# Origin — полный URL фронтенда (протокол + хост + порт)
# Должен ТОЧНО совпадать с тем, откуда браузер делает запросы
WEBAUTHN_ORIGIN = os.environ.get('WEBAUTHN_ORIGIN', 'http://localhost:3000')

# Время жизни WebAuthn challenge в кэше (секунды)
WEBAUTHN_CHALLENGE_TTL = 300  # 5 минут

# ============================================
# CORS — разрешаем запросы с фронтенда
# ============================================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]
CORS_ALLOW_CREDENTIALS = True

# Разрешённые заголовки для CORS запросов
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# ============================================
# REST FRAMEWORK + THROTTLING (rate limiting)
# ============================================
# Throttling защищает от брутфорса и DDoS атак на уровне API.
# Лимиты: anon = анонимные, user = авторизованные пользователи.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Безопасный дефолт: любой новый эндпоинт требует аутентификации.
    # Публичные эндпоинты явно объявляют permission_classes = [AllowAny].
    # Это защищает от случайного раскрытия данных при добавлении нового view.
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),

    # Throttle классы для ограничения запросов
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],

    # Лимиты. Ключи совпадают со scope в throttle-классах (users/throttles.py).
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',          # Анонимные запросы: 100/день
        'user': '1000/day',         # Авторизованные: 1000/день
        'login': '5/min',           # Вход: 5 попыток/минуту
        'send_code': '3/hour',      # Отправка кода: 3/час
        'register': '10/hour',      # Регистрация: 10/час
        'verify_code': '20/hour',   # Проверка кода: 20/час
    },
}

# ============================================
# JWT (JSON Web Token) настройки
# ============================================
SIMPLE_JWT = {
    # Время жизни токенов (баланс между удобством и безопасностью)
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # 60 минут (было 1 день)
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),     # 7 дней

    # Безопасность токенов
    'ROTATE_REFRESH_TOKENS': True,    # Новый refresh при каждом использовании
    'BLACKLIST_AFTER_ROTATION': True,  # Старый refresh в чёрный список

    # Алгоритм подписи — явно один алгоритм, защита от Algorithm Confusion атак
    # (RS256→HS256 downgrade, "none" algorithm bypass)
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),

    # CVE-2024-22513: Проверяем is_active при каждом запросе по токену.
    # Без этого деактивированный пользователь мог использовать токен
    # до истечения его срока действия (до 60 минут).
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    # Добавляем user_id в токен для идентификации
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# ============================================
# EMAIL (Gmail SMTP)
# ============================================
# Credentials загружаются ТОЛЬКО из переменных окружения!
# Никогда не хардкодьте пароли в коде.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get(
    'DEFAULT_FROM_EMAIL',
    f'EduPlatform <{EMAIL_HOST_USER}>'
)

# ============================================
# PRODUCTION SECURITY SETTINGS
# ============================================
# Эти настройки автоматически включаются в production (DEBUG=False)
if not DEBUG:
    # Принудительный редирект на HTTPS
    SECURE_SSL_REDIRECT = True

    # Cookie только по HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS — браузер запоминает, что сайт только HTTPS (1 год)
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Дополнительные заголовки безопасности
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'

# ============================================
# LOGGING — аудит и мониторинг
# ============================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'security': {
            'format': '[{asctime}] SECURITY {levelname}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'security_file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'formatter': 'security',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'users.auth': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
