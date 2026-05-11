"""
Кастомные throttle-классы для ограничения запросов аутентификации.

Rate limiting (ограничение частоты запросов) — серверная защита от:
- Брутфорс атак на пароли
- Массовой рассылки спама через форму регистрации
- Автоматических атак на API

Классы:
- LoginRateThrottle: 5 попыток/минуту для входа
- SendCodeRateThrottle: 3 запроса/час для отправки кода (дорогая операция)
- RegisterRateThrottle: 10 регистраций/час
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """
    Ограничивает попытки входа.
    5 неудачных попыток в минуту → блокировка IP на 1 минуту.
    """
    scope = 'login'
    rate = '5/min'


class SendCodeRateThrottle(AnonRateThrottle):
    """
    Ограничивает отправку verification кодов.
    Отправка email — дорогая операция. 3 запроса/час на IP.
    """
    scope = 'send_code'
    rate = '30/hour'


class RegisterRateThrottle(AnonRateThrottle):
    """
    Ограничивает регистрацию новых аккаунтов.
    10 регистраций/час на IP (защита от создания фейковых аккаунтов).
    """
    scope = 'register'
    rate = '10/hour'


class VerifyCodeRateThrottle(AnonRateThrottle):
    """
    Ограничивает попытки проверки кода.
    20 попыток/час — достаточно для честного пользователя.
    """
    scope = 'verify_code'
    rate = '20/hour'
