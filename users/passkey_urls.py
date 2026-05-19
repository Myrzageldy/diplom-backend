"""
URL-маршруты для WebAuthn / Passkey

Эти маршруты подключены под префиксом /api/auth/
в config/urls.py.

Полные пути:
  POST /api/auth/passkey/register/begin/      — шаг 1 регистрации
  POST /api/auth/passkey/register/complete/   — шаг 2 регистрации
  POST /api/auth/passkey/login/begin/         — шаг 1 входа
  POST /api/auth/passkey/login/complete/      — шаг 2 входа
  GET  /api/auth/passkey/                     — список passkeys
  DELETE /api/auth/passkey/                   — удаление passkey
  PATCH /api/auth/passkey/<id>/               — переименование passkey
"""
from django.urls import path

from .views import (
    PasskeyDetailView,
    PasskeyListView,
    PasskeyLoginBeginView,
    PasskeyLoginCompleteView,
    PasskeyRegisterBeginView,
    PasskeyRegisterCompleteView,
)

urlpatterns = [
    # Регистрация нового passkey (требует аутентификации JWT)
    path('passkey/register/begin/', PasskeyRegisterBeginView.as_view(), name='passkey_register_begin'),
    path('passkey/register/complete/', PasskeyRegisterCompleteView.as_view(), name='passkey_register_complete'),

    # Вход через passkey (публичный)
    path('passkey/login/begin/', PasskeyLoginBeginView.as_view(), name='passkey_login_begin'),
    path('passkey/login/complete/', PasskeyLoginCompleteView.as_view(), name='passkey_login_complete'),

    # Управление passkeys (список, переименование, удаление)
    path('passkey/', PasskeyListView.as_view(), name='passkey_list'),
    path('passkey/<str:passkey_id>/', PasskeyDetailView.as_view(), name='passkey_detail'),
]
