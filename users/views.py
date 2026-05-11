"""
Views — Обработчики запросов (контроллеры)

View получает HTTP запрос и возвращает HTTP ответ.
Это «мозг» API — здесь происходит вся логика.

Поток данных:
1. Фронтенд отправляет POST /api/users/register/ с данными
2. Django направляет запрос в RegisterView
3. View проверяет данные через Serializer
4. Если всё ок — создаёт пользователя и возвращает токены
5. Фронтенд получает JSON ответ

Безопасность:
- Throttling (rate limiting) на всех публичных эндпоинтах
- Только IsAuthenticated для защищённых ресурсов
- Входные данные валидируются через Serializer
"""
import logging
import pyotp
import qrcode
import io
import base64

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.core import signing
from django.conf import settings

from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    SendCodeSerializer, VerifyCodeSerializer
)
from .models import EmailVerification, PasswordResetToken
from .throttles import (
    LoginRateThrottle,
    SendCodeRateThrottle,
    RegisterRateThrottle,
    VerifyCodeRateThrottle,
)

# Логгер для аудита событий безопасности
logger = logging.getLogger('users.auth')


class RegisterView(APIView):
    """
    POST /api/users/register/

    Регистрация нового пользователя.

    Принимает JSON:
    {
        "name": "Имя",
        "email": "email@example.com",
        "password": "password123",
        "password_confirm": "password123",
        "role": "student"
    }
    """
    permission_classes = [AllowAny]
    throttle_classes = [RegisterRateThrottle]  # 10 регистраций/час

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # Аудит лог успешной регистрации
            logger.info(
                'User registered: email=%s role=%s ip=%s',
                user.email,
                user.role,
                self._get_client_ip(request),
            )

            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Регистрация успешна',
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _get_client_ip(request) -> str:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


class LoginView(APIView):
    """
    POST /api/users/login/

    Вход в аккаунт.

    Принимает JSON:
    {
        "email": "email@example.com",
        "password": "password123"
    }

    При неудаче возвращает HTTP 400 (не 401, чтобы не раскрывать существование аккаунта).
    """
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]  # 5 попыток/минуту

    def post(self, request):
        from .models import User
        from django.utils import timezone

        email = request.data.get('email', '').strip().lower()
        ip = self._get_client_ip(request)

        # Проверяем блокировку ДО валидации пароля (не тратим ресурсы)
        try:
            user_check = User.objects.get(email=email)
            if user_check.is_locked():
                remaining = user_check.locked_until - timezone.now()
                mins = int(remaining.total_seconds() // 60) + 1
                logger.warning('Login blocked (lockout): email=%s ip=%s', email, ip)
                return Response({
                    'detail': f'Аккаунт временно заблокирован из-за множества неудачных попыток. Попробуйте через {mins} мин.',
                    'locked': True,
                    'locked_until': user_check.locked_until.isoformat(),
                }, status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            pass  # Не раскрываем существование аккаунта

        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Успешный вход — сбрасываем счётчик
            user.reset_login_attempts()

            # Если у пользователя включена 2FA — возвращаем временный токен
            if user.totp_enabled:
                temp_token = signing.dumps(
                    {'user_id': user.id},
                    salt='totp_login',
                )
                logger.info('Login 2FA required: email=%s ip=%s', user.email, ip)
                return Response({
                    'requires_2fa': True,
                    'temp_token': temp_token,
                }, status=status.HTTP_200_OK)

            logger.info('Login success: email=%s ip=%s', user.email, ip)
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Вход выполнен успешно',
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_200_OK)

        # Неудачная попытка — увеличиваем счётчик
        logger.warning('Login failed: email=%s ip=%s', email, ip)
        try:
            failed_user = User.objects.get(email=email)
            failed_user.record_failed_login()
            remaining_attempts = max(0, 5 - failed_user.login_attempts)

            if failed_user.is_locked():
                return Response({
                    'detail': 'Аккаунт заблокирован на 15 минут из-за множества неудачных попыток.',
                    'locked': True,
                    'locked_until': failed_user.locked_until.isoformat(),
                }, status=status.HTTP_403_FORBIDDEN)

            errors = dict(serializer.errors)
            if remaining_attempts > 0:
                errors['detail'] = f'Неверный email или пароль. Осталось попыток: {remaining_attempts}'
            else:
                errors['detail'] = 'Неверный email или пароль.'
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            pass

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _get_client_ip(request) -> str:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


class UserProfileView(APIView):
    """
    GET /api/users/profile/  — получить профиль
    PUT /api/users/profile/  — обновить имя

    Требует заголовок: Authorization: Bearer <access_token>
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        name = request.data.get('name', '').strip()

        if not name:
            return Response(
                {'name': ['Имя не может быть пустым']},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(name) > 150:
            return Response(
                {'name': ['Имя слишком длинное (максимум 150 символов)']},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.name = name
        user.save(update_fields=['name'])

        return Response({
            'message': 'Профиль обновлён',
            'user': UserSerializer(user).data
        })


class LogoutView(APIView):
    """
    POST /api/users/logout/

    Выход из аккаунта — добавляет refresh токен в чёрный список.
    После этого токен нельзя использовать даже до истечения срока.

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
                token = RefreshToken(refresh_token)
                token.blacklist()

            logger.info('Logout: user=%s', request.user.email)
            return Response({'message': 'Выход выполнен успешно'}, status=status.HTTP_200_OK)
        except Exception:
            # Даже если токен уже в чёрном списке — выход засчитываем
            return Response({'message': 'Выход выполнен'}, status=status.HTTP_200_OK)


class SendCodeView(APIView):
    """
    POST /api/users/send-code/

    Отправляет 6-значный код верификации на email.
    Rate limit: 3 запроса/час (дорогая операция — SMTP).

    Принимает JSON:
    {
        "email": "email@example.com"
    }
    """
    permission_classes = [AllowAny]
    throttle_classes = [SendCodeRateThrottle]  # 3 кода/час

    def post(self, request):
        serializer = SendCodeSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']

            # Удаляем старые коды для этого email
            EmailVerification.objects.filter(email=email).delete()

            # Генерируем новый код
            code = EmailVerification.generate_code()
            EmailVerification.objects.create(email=email, code=code)

            # Отправляем email
            send_mail(
                subject='Код подтверждения — EduPlatform',
                message=(
                    f'Ваш код подтверждения: {code}\n\n'
                    f'Код действителен 10 минут.\n\n'
                    f'Если вы не запрашивали код — проигнорируйте это письмо.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            logger.info('Verification code sent to: %s', email)
            return Response({'message': 'Код отправлен на email'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyCodeView(APIView):
    """
    POST /api/users/verify-code/

    Проверяет код верификации email.
    Rate limit: 20 попыток/час.

    Принимает JSON:
    {
        "email": "email@example.com",
        "code": "123456"
    }
    """
    permission_classes = [AllowAny]
    throttle_classes = [VerifyCodeRateThrottle]  # 20 попыток/час

    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)

        if serializer.is_valid():
            verification = serializer.validated_data['verification']
            verification.is_verified = True
            verification.save()

            return Response({
                'message': 'Email подтверждён',
                'verified': True
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TOTPSetupView(APIView):
    """
    GET  /api/users/2fa/setup/  — генерирует секрет и QR-код
    POST /api/users/2fa/setup/  — подтверждает первый код и включает 2FA
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Генерируем новый секрет (не сохраняем пока — только показываем)
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        # URI для QR-кода (формат otpauth://)
        uri = totp.provisioning_uri(
            name=user.email,
            issuer_name='EduPlatform'
        )
        # Генерируем QR-код как base64 PNG
        qr = qrcode.make(uri)
        buffer = io.BytesIO()
        qr.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        # Временно сохраняем секрет в поле (не включаем 2FA пока)
        user.totp_secret = secret
        user.save(update_fields=['totp_secret'])

        return Response({
            'secret': secret,
            'qr_code': f'data:image/png;base64,{qr_base64}',
            'uri': uri,
        })

    def post(self, request):
        """Проверяет первый код и включает 2FA"""
        user = request.user
        code = request.data.get('code', '').strip()

        if not user.totp_secret:
            return Response(
                {'detail': 'Сначала получите QR-код'},
                status=status.HTTP_400_BAD_REQUEST
            )

        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code, valid_window=1):
            return Response(
                {'detail': 'Неверный код. Проверьте время на устройстве'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.totp_enabled = True
        user.save(update_fields=['totp_enabled'])

        logger.info('2FA enabled: user=%s', user.email)
        return Response({'message': '2FA успешно включена'})


class TOTPDisableView(APIView):
    """
    POST /api/users/2fa/disable/  — отключает 2FA (требует пароль + код)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        password = request.data.get('password', '')
        code = request.data.get('code', '').strip()

        if not user.check_password(password):
            return Response(
                {'detail': 'Неверный пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.totp_enabled:
            totp = pyotp.TOTP(user.totp_secret)
            if not totp.verify(code, valid_window=1):
                return Response(
                    {'detail': 'Неверный код аутентификатора'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        user.totp_enabled = False
        user.totp_secret = ''
        user.save(update_fields=['totp_enabled', 'totp_secret'])

        logger.info('2FA disabled: user=%s', user.email)
        return Response({'message': '2FA отключена'})


class TOTPLoginVerifyView(APIView):
    """
    POST /api/users/2fa/verify-login/

    Второй шаг входа при включённой 2FA.
    Принимает временный токен + TOTP код, возвращает полные JWT токены.

    {
        "temp_token": "...",
        "code": "123456"
    }
    """
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        from .models import User

        temp_token = request.data.get('temp_token', '')
        code = request.data.get('code', '').strip()

        if not temp_token or not code:
            return Response(
                {'detail': 'Требуется temp_token и code'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем временный токен (действителен 5 минут)
        try:
            data = signing.loads(temp_token, salt='totp_login', max_age=300)
            user = User.objects.get(id=data['user_id'])
        except (signing.SignatureExpired, signing.BadSignature):
            return Response(
                {'detail': 'Токен истёк или недействителен. Войдите заново'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except User.DoesNotExist:
            return Response(
                {'detail': 'Пользователь не найден'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем TOTP код
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code, valid_window=1):
            logger.warning('2FA login failed: user=%s ip=%s', user.email, self._get_client_ip(request))
            return Response(
                {'detail': 'Неверный код. Попробуйте ещё раз'},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info('Login success (2FA): email=%s ip=%s', user.email, self._get_client_ip(request))
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Вход выполнен успешно',
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        })

    @staticmethod
    def _get_client_ip(request) -> str:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


class PasswordResetRequestView(APIView):
    """
    POST /api/users/password-reset/

    Запрос на сброс пароля. Принимает email, отправляет письмо со ссылкой.
    Не раскрывает существование аккаунта (всегда возвращает 200).
    Rate limit: 3 запроса/час.

    {
        "email": "user@example.com"
    }
    """
    permission_classes = [AllowAny]
    throttle_classes = [SendCodeRateThrottle]

    def post(self, request):
        from .models import User
        email = request.data.get('email', '').strip().lower()

        if not email:
            return Response(
                {'detail': 'Email обязателен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Не раскрываем существование аккаунта — всегда 200
        try:
            user = User.objects.get(email=email)

            # Удаляем старые токены пользователя
            PasswordResetToken.objects.filter(user=user).delete()

            # Создаём новый токен
            token_obj = PasswordResetToken.objects.create(user=user)

            # Ссылка для сброса (фронтенд)
            reset_link = f'http://localhost:3000/reset-password/{token_obj.token}'

            send_mail(
                subject='Сброс пароля — EduPlatform',
                message=(
                    f'Здравствуйте, {user.name}!\n\n'
                    f'Вы запросили сброс пароля для аккаунта {email}.\n\n'
                    f'Перейдите по ссылке для установки нового пароля:\n{reset_link}\n\n'
                    f'Ссылка действительна 1 час.\n\n'
                    f'Если вы не запрашивали сброс пароля — проигнорируйте это письмо.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            logger.info('Password reset requested: email=%s ip=%s', email, self._get_client_ip(request))

        except User.DoesNotExist:
            # Намеренно не сообщаем что email не найден
            logger.warning('Password reset for non-existent email: %s', email)

        return Response({
            'message': 'Если аккаунт с таким email существует, на него отправлена ссылка для сброса пароля'
        })

    @staticmethod
    def _get_client_ip(request) -> str:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


class PasswordResetConfirmView(APIView):
    """
    POST /api/users/password-reset/confirm/

    Установка нового пароля по токену из письма.

    {
        "token": "uuid-токен-из-ссылки",
        "password": "новый_пароль",
        "password_confirm": "новый_пароль"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        token_str = request.data.get('token', '').strip()
        password = request.data.get('password', '')
        password_confirm = request.data.get('password_confirm', '')

        if not token_str or not password or not password_confirm:
            return Response(
                {'detail': 'Все поля обязательны'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if password != password_confirm:
            return Response(
                {'password_confirm': 'Пароли не совпадают'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(password) < 8:
            return Response(
                {'password': 'Пароль должен содержать минимум 8 символов'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token_obj = PasswordResetToken.objects.select_related('user').get(token=token_str)
        except (PasswordResetToken.DoesNotExist, ValueError):
            return Response(
                {'detail': 'Ссылка недействительна или устарела'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if token_obj.is_expired():
            token_obj.delete()
            return Response(
                {'detail': 'Ссылка истекла. Запросите сброс пароля заново'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = token_obj.user
        user.set_password(password)
        user.save(update_fields=['password'])

        # Удаляем токен после использования
        token_obj.delete()

        logger.info('Password reset confirmed: user=%s', user.email)
        return Response({'message': 'Пароль успешно изменён. Теперь вы можете войти'})


class DeleteAccountView(APIView):
    """
    DELETE /api/users/delete-account/

    Удаляет аккаунт пользователя вместе со всеми данными.
    Требует подтверждение текущим паролем.

    Принимает JSON:
    {
        "password": "current_password",
        "refresh": "refresh_token_here"  (необязательно)
    }
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        password = request.data.get('password', '')

        if not password:
            return Response(
                {'detail': 'Введите пароль для подтверждения'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.check_password(password):
            return Response(
                {'detail': 'Неверный пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Инвалидируем refresh токен если передан
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass

        email = user.email
        user.delete()
        logger.info('DeleteAccount: user=%s', email)

        return Response({'message': 'Аккаунт удалён'}, status=status.HTTP_200_OK)
