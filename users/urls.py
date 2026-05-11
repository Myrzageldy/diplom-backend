"""
URLs для приложения users

Каждый path() связывает URL с View.
Например: /api/users/register/ -> RegisterView
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView, LoginView, UserProfileView, LogoutView,
    SendCodeView, VerifyCodeView, DeleteAccountView,
    TOTPSetupView, TOTPDisableView, TOTPLoginVerifyView,
    PasswordResetRequestView, PasswordResetConfirmView,
)

urlpatterns = [
    # Верификация email (пошаговая регистрация)
    path('send-code/', SendCodeView.as_view(), name='send_code'),
    path('verify-code/', VerifyCodeView.as_view(), name='verify_code'),

    # Регистрация
    path('register/', RegisterView.as_view(), name='register'),

    # Вход
    path('login/', LoginView.as_view(), name='login'),

    # Выход
    path('logout/', LogoutView.as_view(), name='logout'),

    # Профиль пользователя
    path('profile/', UserProfileView.as_view(), name='profile'),

    # Удаление аккаунта
    path('delete-account/', DeleteAccountView.as_view(), name='delete_account'),

    # Обновление access токена
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Двухфакторная аутентификация (2FA / TOTP)
    path('2fa/setup/', TOTPSetupView.as_view(), name='totp_setup'),
    path('2fa/disable/', TOTPDisableView.as_view(), name='totp_disable'),
    path('2fa/verify-login/', TOTPLoginVerifyView.as_view(), name='totp_verify_login'),

    # Сброс пароля
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
