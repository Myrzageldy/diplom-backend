"""
Миграция 0007: Добавление WebAuthn/Passkey моделей

Добавляет:
- WebAuthnCredential — хранение passkey ключей пользователей
- PasskeyLoginLog — журнал аудита входов через Passkey
"""
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_add_login_lockout'),
    ]

    operations = [
        # Таблица для хранения WebAuthn credential (passkey)
        migrations.CreateModel(
            name='WebAuthnCredential',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                    verbose_name='UUID'
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='webauthn_credentials',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Пользователь'
                )),
                ('credential_id', models.BinaryField(
                    db_index=True,
                    unique=True,
                    verbose_name='ID учётных данных'
                )),
                ('public_key', models.BinaryField(
                    verbose_name='Публичный ключ (COSE/CBOR)'
                )),
                ('sign_count', models.PositiveBigIntegerField(
                    default=0,
                    verbose_name='Счётчик подписей'
                )),
                ('transports', models.JSONField(
                    default=list,
                    verbose_name='Транспортные протоколы'
                )),
                ('name', models.CharField(
                    default='Мой Passkey',
                    max_length=100,
                    verbose_name='Название ключа'
                )),
                ('device_type', models.CharField(
                    choices=[
                        ('platform', 'Встроенный (Windows Hello, Touch ID, Face ID)'),
                        ('cross-platform', 'Внешний (USB, NFC, Bluetooth)'),
                    ],
                    default='platform',
                    max_length=20,
                    verbose_name='Тип устройства'
                )),
                ('backed_up', models.BooleanField(
                    default=False,
                    verbose_name='Синхронизирован в облаке'
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True,
                    verbose_name='Дата добавления'
                )),
                ('last_used_at', models.DateTimeField(
                    blank=True,
                    null=True,
                    verbose_name='Последнее использование'
                )),
            ],
            options={
                'verbose_name': 'WebAuthn / Passkey',
                'verbose_name_plural': 'WebAuthn / Passkeys',
                'ordering': ['-created_at'],
            },
        ),
        # Таблица журнала аудита входов через Passkey
        migrations.CreateModel(
            name='PasskeyLoginLog',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID'
                )),
                ('user', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='passkey_login_logs',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Пользователь'
                )),
                ('ip', models.GenericIPAddressField(
                    verbose_name='IP адрес'
                )),
                ('user_agent', models.TextField(
                    blank=True,
                    verbose_name='User-Agent браузера'
                )),
                ('success', models.BooleanField(
                    verbose_name='Успешно'
                )),
                ('error_message', models.CharField(
                    blank=True,
                    max_length=500,
                    verbose_name='Сообщение об ошибке'
                )),
                ('timestamp', models.DateTimeField(
                    auto_now_add=True,
                    verbose_name='Время попытки'
                )),
            ],
            options={
                'verbose_name': 'Лог входа Passkey',
                'verbose_name_plural': 'Логи входов Passkey',
                'ordering': ['-timestamp'],
            },
        ),
    ]
