"""
Serializers - Сериализаторы (преобразователи данных)

Сериализатор делает две вещи:
1. Проверяет входящие данные (валидация)
2. Преобразует данные Python <-> JSON

Пример:
- Фронтенд отправляет JSON: {"email": "test@mail.com", "password": "123"}
- Serializer проверяет: email валидный? password не пустой?
- Если всё ок - создаёт объект Python для работы
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, EmailVerification


class RegisterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации.

    Принимает: name, email, password, password_confirm, role
    Возвращает: данные созданного пользователя
    """

    # Дополнительные поля (не из модели)
    password = serializers.CharField(
        write_only=True,  # Не возвращать в ответе
        min_length=8,
        error_messages={
            'min_length': 'Пароль должен содержать минимум 8 символов'
        }
    )
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(
        choices=User.ROLE_CHOICES,
        default='student'
    )

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password', 'password_confirm', 'role']
        # id - только для чтения (генерируется автоматически)
        read_only_fields = ['id']

    def validate_email(self, value):
        """Проверка email на уникальность"""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует')
        return value.lower()

    def validate(self, data):
        """Проверка что пароли совпадают"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Пароли не совпадают'
            })
        return data

    def create(self, validated_data):
        """Создание пользователя"""
        # Убираем password_confirm - его нет в модели
        validated_data.pop('password_confirm')

        # Создаём пользователя через менеджер (чтобы пароль захешировался)
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password'],
            role=validated_data.get('role', 'student')
        )

        # Привязываем коды верификации к пользователю
        EmailVerification.objects.filter(email=user.email).update(user=user)

        return user


class LoginSerializer(serializers.Serializer):
    """
    Сериализатор для входа.

    Принимает: email, password
    Возвращает: данные пользователя (если вход успешен)
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Проверка учётных данных"""
        email = data.get('email', '').lower()
        password = data.get('password', '')

        # authenticate - встроенная функция Django для проверки логина/пароля
        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError({
                'detail': 'Неверный email или пароль'
            })

        if not user.is_active:
            raise serializers.ValidationError({
                'detail': 'Аккаунт деактивирован'
            })

        # Сохраняем пользователя для использования во view
        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения данных пользователя.
    Используется когда нужно вернуть информацию о пользователе.
    """

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'date_joined', 'totp_enabled']
        read_only_fields = ['id', 'email', 'role', 'date_joined', 'totp_enabled']


class SendCodeSerializer(serializers.Serializer):
    """
    Сериализатор для отправки кода верификации.
    Принимает: email
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        """Проверяем что email ещё не зарегистрирован"""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует')
        return value.lower()


class VerifyCodeSerializer(serializers.Serializer):
    """
    Сериализатор для проверки кода верификации.
    Принимает: email, code
    """
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, data):
        """Проверяем код"""
        email = data.get('email', '').lower()
        code = data.get('code', '')

        # Ищем последний код для этого email
        verification = EmailVerification.objects.filter(
            email=email,
            code=code,
            is_verified=False
        ).order_by('-created_at').first()

        if not verification:
            raise serializers.ValidationError({
                'code': 'Неверный код'
            })

        if verification.is_expired():
            raise serializers.ValidationError({
                'code': 'Код истёк. Запросите новый'
            })

        # Сохраняем для использования во view
        data['verification'] = verification
        return data
