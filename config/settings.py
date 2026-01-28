"""
Django settings - Настройки проекта

Это главный файл настроек Django. Здесь указываем:
- Какие приложения используем
- Как подключаться к базе данных
- Настройки безопасности
"""
from pathlib import Path
from datetime import timedelta
import os

# Корневая папка проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Секретный ключ для шифрования (в продакшене хранить в .env!)
SECRET_KEY = 'django-insecure-change-this-in-production-12345'

# Режим разработки (True = показывать ошибки)
DEBUG = True

# Какие домены могут обращаться к серверу
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# ============================================
# ПРИЛОЖЕНИЯ (Apps)
# ============================================
# Django работает через "приложения" - модули с определённой функцией
INSTALLED_APPS = [
    # Встроенные приложения Django
    'django.contrib.admin',          # Админ-панель
    'django.contrib.auth',           # Система авторизации
    'django.contrib.contenttypes',   # Типы контента
    'django.contrib.sessions',       # Сессии пользователей
    'django.contrib.messages',       # Сообщения
    'django.contrib.staticfiles',    # Статические файлы (CSS, JS)

    # Сторонние библиотеки
    'rest_framework',                # REST API framework
    'corsheaders',                   # Разрешает запросы с фронтенда
    'rest_framework_simplejwt',      # JWT токены

    # Наши приложения
    'users',                         # Приложение для пользователей
    'courses',                       # Приложение для курсов
]

# ============================================
# MIDDLEWARE (Промежуточные обработчики)
# ============================================
# Каждый запрос проходит через эти "фильтры"
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',     # CORS - должен быть первым!
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Главный файл с URL маршрутами
ROOT_URLCONF = 'config.urls'

# Настройки шаблонов (для админки)
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
# SQLite - простая база данных в виде файла
# Для продакшена лучше PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ============================================
# КАСТОМНАЯ МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ
# ============================================
# Вместо стандартного User используем свою модель
AUTH_USER_MODEL = 'users.User'

# Валидация паролей
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
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

# Статические файлы
STATIC_URL = 'static/'

# Медиафайлы (загружаемые пользователями)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# CORS - Разрешаем фронтенду обращаться к API
# ============================================
# Это нужно потому что фронтенд (localhost:3000) и бэкенд (localhost:8000)
# работают на разных портах - браузер блокирует такие запросы без CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",      # Next.js dev server
    "http://127.0.0.1:3000",
    "http://localhost:3001",      # Next.js альтернативный порт
    "http://127.0.0.1:3001",
]
CORS_ALLOW_CREDENTIALS = True

# ============================================
# REST FRAMEWORK настройки
# ============================================
REST_FRAMEWORK = {
    # Как аутентифицировать пользователей
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Доступ по умолчанию - для всех
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
}

# ============================================
# JWT (JSON Web Token) настройки
# ============================================
# JWT - это "пропуск" пользователя. После логина он получает токен,
# и при каждом запросе отправляет его в заголовке Authorization
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),      # Токен живёт 1 день
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),     # Refresh токен - 7 дней
    'ROTATE_REFRESH_TOKENS': True,                   # Обновлять refresh при использовании
    'AUTH_HEADER_TYPES': ('Bearer',),                # Формат: "Bearer <token>"
}

# ============================================
# EMAIL настройки (Gmail SMTP)
# ============================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'smitdzo6434@gmail.com'
EMAIL_HOST_PASSWORD = 'qtxz vwek kdmb lwkr'
DEFAULT_FROM_EMAIL = 'EduPlatform <smitdzo6434@gmail.com>'
