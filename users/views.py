"""
Views - Обработчики запросов (контроллеры)

View получает HTTP запрос и возвращает HTTP ответ.
Это как "мозг" API - здесь происходит вся логика.

Пример потока данных:
1. Фронтенд отправляет POST /api/users/register/ с данными
2. Django направляет запрос в RegisterView
3. View проверяет данные через Serializer
4. Если всё ок - создаёт пользователя и возвращает токены
5. Фронтенд получает JSON ответ
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings

from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    SendCodeSerializer, VerifyCodeSerializer
)
from .models import EmailVerification


class RegisterView(APIView):
    """
    POST /api/users/register/

    Регистрация нового пользователя.

    Принимает JSON:
    {
        "name": "Имя",
        "email": "email@example.com",
        "password": "password123",
        "password_confirm": "password123"
    }

    Возвращает:
    {
        "user": { ... },
        "tokens": {
            "access": "...",
            "refresh": "..."
        }
    }
    """
    permission_classes = [AllowAny]  # Доступно всем (без авторизации)

    def post(self, request):
        # Создаём сериализатор с данными из запроса
        serializer = RegisterSerializer(data=request.data)

        # is_valid() проверяет все правила валидации
        if serializer.is_valid():
            # save() вызывает метод create() в сериализаторе
            user = serializer.save()

            # Генерируем JWT токены для нового пользователя
            refresh = RefreshToken.for_user(user)

            return Response({
                'message': 'Регистрация успешна',
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_201_CREATED)

        # Если данные не валидны - возвращаем ошибки
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    POST /api/users/login/

    Вход в аккаунт.

    Принимает JSON:
    {
        "email": "email@example.com",
        "password": "password123"
    }

    Возвращает:
    {
        "user": { ... },
        "tokens": {
            "access": "...",
            "refresh": "..."
        }
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            # Пользователь уже проверен в serializer.validate()
            user = serializer.validated_data['user']

            # Генерируем токены
            refresh = RefreshToken.for_user(user)

            return Response({
                'message': 'Вход выполнен успешно',
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    GET /api/users/profile/
    PUT /api/users/profile/

    Получение и обновление профиля текущего пользователя.
    Требует авторизации (токен в заголовке).

    Заголовок: Authorization: Bearer <access_token>

    GET Возвращает:
    {
        "id": 1,
        "email": "email@example.com",
        "name": "Имя",
        "role": "student",
        "date_joined": "2024-01-15T12:00:00Z"
    }

    PUT Принимает:
    {
        "name": "Новое имя"
    }
    """
    permission_classes = [IsAuthenticated]  # Только авторизованные

    def get(self, request):
        # request.user - текущий авторизованный пользователь
        # Django автоматически определяет его по токену
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        # Обновление профиля
        user = request.user
        name = request.data.get('name')

        if name:
            user.name = name
            user.save()

        return Response({
            'message': 'Профиль обновлён',
            'user': UserSerializer(user).data
        })


class LogoutView(APIView):
    """
    POST /api/users/logout/

    Выход из аккаунта (инвалидация refresh токена).

    Принимает JSON:
    {
        "refresh": "refresh_token_here"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                # Добавляем токен в чёрный список
                token = RefreshToken(refresh_token)
                token.blacklist()

            return Response({
                'message': 'Выход выполнен успешно'
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({
                'message': 'Выход выполнен'
            }, status=status.HTTP_200_OK)


class SendCodeView(APIView):
    """
    POST /api/users/send-code/

    Отправляет код верификации на email.

    Принимает JSON:
    {
        "email": "email@example.com"
    }

    Возвращает:
    {
        "message": "Код отправлен на email"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendCodeSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']

            # Удаляем старые коды для этого email
            EmailVerification.objects.filter(email=email).delete()

            # Генерируем новый код
            code = EmailVerification.generate_code()

            # Сохраняем в базу
            EmailVerification.objects.create(email=email, code=code)

            # Отправляем email
            send_mail(
                subject='Код подтверждения - EduPlatform',
                message=f'Ваш код подтверждения: {code}\n\nКод действителен 10 минут.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            return Response({
                'message': 'Код отправлен на email'
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyCodeView(APIView):
    """
    POST /api/users/verify-code/

    Проверяет код верификации.

    Принимает JSON:
    {
        "email": "email@example.com",
        "code": "123456"
    }

    Возвращает:
    {
        "message": "Email подтверждён",
        "verified": true
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)

        if serializer.is_valid():
            verification = serializer.validated_data['verification']

            # Помечаем как подтверждённый
            verification.is_verified = True
            verification.save()

            return Response({
                'message': 'Email подтверждён',
                'verified': True
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
