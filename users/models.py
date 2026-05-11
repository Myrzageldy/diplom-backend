"""
Models - Модели данных (структура базы данных)

Модель - это описание таблицы в базе данных.
Каждое поле модели = колонка в таблице.

User - модель пользователя с полями:
- email (уникальный, используется для входа)
- name (имя пользователя)
- password (хранится в зашифрованном виде)
- role (роль: student или teacher)
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import random
import string
import uuid
from django.utils import timezone
from datetime import timedelta


class UserManager(BaseUserManager):
    """
    Менеджер для создания пользователей.
    Django требует это для кастомной модели User.
    """

    def create_user(self, email, name, password=None, role='student'):
        """Создаёт обычного пользователя"""
        if not email:
            raise ValueError('Email обязателен')

        # normalize_email делает email@MAIL.com -> email@mail.com
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, role=role)

        # set_password() хеширует пароль (шифрует)
        # В базе хранится не "123456", а что-то типа "pbkdf2_sha256$..."
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None):
        """Создаёт администратора (для admin-панели)"""
        user = self.create_user(email, name, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    Модель пользователя.

    AbstractBaseUser - базовый класс Django для пользователей
    PermissionsMixin - добавляет права доступа (is_superuser и т.д.)
    """

    # Роли пользователей
    ROLE_CHOICES = [
        ('student', 'Ученик'),
        ('teacher', 'Преподаватель'),
    ]

    # Поля таблицы
    email = models.EmailField(
        unique=True,  # Нельзя два пользователя с одним email
        verbose_name='Email'
    )
    name = models.CharField(
        max_length=150,
        verbose_name='Имя'
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='student',
        verbose_name='Роль'
    )

    # Служебные поля
    is_active = models.BooleanField(default=True)   # Активен ли аккаунт
    is_staff = models.BooleanField(default=False)   # Доступ в админку
    date_joined = models.DateTimeField(auto_now_add=True)  # Дата регистрации

    # Двухфакторная аутентификация (TOTP)
    totp_secret = models.CharField(max_length=64, blank=True, default='', verbose_name='TOTP секрет')
    totp_enabled = models.BooleanField(default=False, verbose_name='2FA включена')

    # Защита от перебора паролей
    login_attempts = models.PositiveSmallIntegerField(default=0, verbose_name='Неудачные попытки входа')
    locked_until = models.DateTimeField(null=True, blank=True, verbose_name='Заблокирован до')

    # Указываем что для входа используется email (не username)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']  # Обязательные поля при создании через CLI

    # Подключаем менеджер
    objects = UserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email

    def is_locked(self) -> bool:
        """Проверяет, заблокирован ли аккаунт в данный момент"""
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False

    def record_failed_login(self):
        """
        Увеличивает счётчик неудачных попыток.
        При достижении 5 — блокирует аккаунт на 15 минут.
        """
        self.login_attempts += 1
        if self.login_attempts >= 5:
            self.locked_until = timezone.now() + timedelta(minutes=15)
        self.save(update_fields=['login_attempts', 'locked_until'])

    def reset_login_attempts(self):
        """Сбрасывает счётчик после успешного входа"""
        if self.login_attempts > 0 or self.locked_until:
            self.login_attempts = 0
            self.locked_until = None
            self.save(update_fields=['login_attempts', 'locked_until'])


class EmailVerification(models.Model):
    """
    Модель для хранения кодов верификации email.

    Когда пользователь вводит email при регистрации,
    мы генерируем 6-значный код и отправляем на почту.
    Код действителен 10 минут.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verification_codes',
        verbose_name='Пользователь',
        null=True,
        blank=True
    )
    email = models.EmailField(verbose_name='Email')
    code = models.CharField(max_length=6, verbose_name='Код')
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False, verbose_name='Подтверждён')

    class Meta:
        verbose_name = 'Код верификации'
        verbose_name_plural = 'Коды верификации'

    def __str__(self):
        return f'{self.email} - {self.code}'

    @staticmethod
    def generate_code():
        """Генерирует случайный 6-значный код"""
        return ''.join(random.choices(string.digits, k=6))

    def is_expired(self):
        """Проверяет истёк ли код (10 минут)"""
        return timezone.now() > self.created_at + timedelta(minutes=10)


class PasswordResetToken(models.Model):
    """
    Токен для сброса пароля.

    Когда пользователь нажимает «Забыл пароль», генерируется UUID-токен.
    Ссылка со токеном отправляется на email. Токен действителен 1 час.
    После использования токен удаляется.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
        verbose_name='Пользователь'
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name='Токен')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Токен сброса пароля'
        verbose_name_plural = 'Токены сброса пароля'

    def __str__(self):
        return f'{self.user.email} - {self.token}'

    def is_expired(self):
        """Токен действителен 1 час"""
        return timezone.now() > self.created_at + timedelta(hours=1)
