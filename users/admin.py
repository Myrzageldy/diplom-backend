"""
Admin - Настройка админ-панели Django

Админ-панель позволяет управлять данными через браузер.
После запуска сервера доступна по адресу: http://localhost:8000/admin/
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailVerification


class EmailVerificationInline(admin.TabularInline):
    """Показывает коды верификации внутри страницы пользователя"""
    model = EmailVerification
    fk_name = 'user'
    extra = 0
    readonly_fields = ['email', 'code', 'is_verified', 'created_at']
    can_delete = True
    max_num = 0  # Нельзя добавлять новые через админку


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Настройка отображения User в админке"""

    list_display = ['email', 'name', 'role', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'name']
    ordering = ['-date_joined']

    # Добавляем inline с кодами верификации
    inlines = [EmailVerificationInline]

    # Поля при редактировании пользователя
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личная информация', {'fields': ('name', 'role')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

    # Поля при создании пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'role', 'password1', 'password2'),
        }),
    )

