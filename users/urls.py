"""
URLs для приложения users

Каждый path() связывает URL с View.
Например: /api/users/register/ -> RegisterView
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView, LoginView, UserProfileView, LogoutView,
    SendCodeView, VerifyCodeView
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

    # Обновление access токена (встроенный view из simplejwt)
    # Когда access токен истёк, фронтенд отправляет refresh токен сюда
    # и получает новый access токен
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
