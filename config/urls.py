"""
URL Configuration - Маршруты API

Это как "карта дорог" для запросов.
Когда приходит запрос на /api/users/register/,
Django смотрит сюда и направляет его в нужное место.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Админ-панель Django (можно смотреть данные в браузере)
    path('admin/', admin.site.urls),

    # Все запросы начинающиеся с /api/users/ идут в users/urls.py
    path('api/users/', include('users.urls')),

    # WebAuthn / Passkey endpoints — /api/auth/passkey/...
    path('api/auth/', include('users.passkey_urls')),

    # Все запросы начинающиеся с /api/courses/ идут в courses/urls.py
    path('api/courses/', include('courses.urls')),
]

# Для отображения медиафайлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
