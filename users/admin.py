"""
Admin - Настройка админ-панели Django

Админ-панель позволяет управлять данными через браузер.
После запуска сервера доступна по адресу: http://localhost:8000/admin/
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailVerification, WebAuthnCredential, PasskeyLoginLog


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


@admin.register(WebAuthnCredential)
class WebAuthnCredentialAdmin(admin.ModelAdmin):
    """WebAuthn / Passkey ключи в админке"""
    list_display = ['user', 'name', 'device_type', 'backed_up', 'sign_count', 'created_at', 'last_used_at']
    list_filter = ['device_type', 'backed_up']
    search_fields = ['user__email', 'name']
    readonly_fields = ['id', 'credential_id', 'public_key', 'sign_count', 'transports', 'created_at', 'last_used_at']
    ordering = ['-created_at']


@admin.register(PasskeyLoginLog)
class PasskeyLoginLogAdmin(admin.ModelAdmin):
    """Журнал входов через Passkey в админке"""
    list_display = ['user', 'success', 'ip', 'timestamp', 'error_message']
    list_filter = ['success']
    search_fields = ['user__email', 'ip']
    readonly_fields = ['user', 'ip', 'user_agent', 'success', 'error_message', 'timestamp']
    ordering = ['-timestamp']

    def has_add_permission(self, request):
        return False  # Логи нельзя создавать вручную

