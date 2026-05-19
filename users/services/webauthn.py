"""
services/webauthn.py — Бизнес-логика WebAuthn / Passkey

Этот модуль содержит всю бизнес-логику аутентификации через Passkey:
1. begin_registration()   — генерация challenge для регистрации нового passkey
2. complete_registration() — верификация и сохранение нового passkey
3. begin_login()           — генерация challenge для входа через passkey
4. complete_login()        — верификация подписи и идентификация пользователя

Архитектурный принцип: Views только принимают HTTP-запросы и возвращают ответы.
Вся логика (шифрование, база данных, кэш) — здесь, в сервисном слое.
Это упрощает тестирование и поддержку кода.

Зависимости:
  pip install webauthn==2.2.0
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

from django.core.cache import cache
from django.utils import timezone

import webauthn
from webauthn import (
    base64url_to_bytes,
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import bytes_to_base64url
from webauthn.helpers.cose import COSEAlgorithmIdentifier
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorAssertionResponse,
    AuthenticatorAttestationResponse,
    AuthenticatorSelectionCriteria,
    AuthenticatorTransport,
    AuthenticationCredential,
    PublicKeyCredentialDescriptor,
    PublicKeyCredentialType,
    RegistrationCredential,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from ..models import PasskeyLoginLog, User, WebAuthnCredential

logger = logging.getLogger('users.auth')

# RP (Relying Party) — наш сервер, которому доверяет аутентификатор
RP_ID = 'localhost'
RP_NAME = 'EduPlatform KZ'

# Origin, с которого ожидаем запросы (фронтенд)
EXPECTED_ORIGIN = 'http://localhost:3000'

# Время жизни challenge в кэше (5 минут = 300 секунд)
CHALLENGE_TTL = 300

# Таймаут WebAuthn церемонии (60 секунд)
CEREMONY_TIMEOUT_MS = 60_000

# Поддерживаемые алгоритмы подписи:
# ES256 (-7)  — ECDSA с SHA-256, ключ P-256 (предпочтительный, более быстрый)
# RS256 (-257) — RSASSA-PKCS1 с SHA-256 (запасной, совместимость с USB-ключами)
SUPPORTED_ALGORITHMS = [
    COSEAlgorithmIdentifier.ECDSA_SHA_256,
    COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
]


def _make_session_id() -> str:
    """Генерирует криптографически случайный ID сессии (32 символа hex)."""
    return os.urandom(16).hex()


def _parse_transports(raw_transports: list[str]) -> list[AuthenticatorTransport]:
    """
    Конвертирует строки транспортов в enum-значения py_webauthn.

    Браузер возвращает: ["internal"], ["usb"], ["nfc", "ble"], ["hybrid"] и т.д.
    """
    mapping = {
        'usb': AuthenticatorTransport.USB,
        'nfc': AuthenticatorTransport.NFC,
        'ble': AuthenticatorTransport.BLE,
        'smart-card': AuthenticatorTransport.SMART_CARD,
        'hybrid': AuthenticatorTransport.HYBRID,
        'internal': AuthenticatorTransport.INTERNAL,
    }
    return [mapping[t] for t in raw_transports if t in mapping]


def _detect_device_type(transports: list[str]) -> str:
    """
    Определяет тип устройства по транспортному протоколу.

    'internal' = встроенный аутентификатор (Windows Hello PIN, Touch ID, Face ID)
    всё остальное = внешний ключ (USB YubiKey, NFC-карта, Bluetooth)
    """
    return 'platform' if 'internal' in transports else 'cross-platform'


# ────────────────────────────────────────────────────────────────────────────────
# РЕГИСТРАЦИЯ PASSKEY
# ────────────────────────────────────────────────────────────────────────────────

def begin_registration(user: User) -> dict[str, Any]:
    """
    Шаг 1 регистрации: генерирует PublicKeyCredentialCreationOptions.

    Что происходит:
    1. Генерируем cryptographically random challenge (32 байта из /dev/urandom)
    2. Формируем список уже существующих ключей (excludeCredentials)
       — браузер покажет ошибку если ключ уже зарегистрирован
    3. Сохраняем challenge в кэш с TTL 5 минут
    4. Возвращаем опции для передачи в navigator.credentials.create()

    Returns:
        {'options': dict, 'session_id': str}
    """
    # Ключи, которые уже зарегистрированы у этого пользователя.
    # Передаём в excludeCredentials — браузер откажет в повторной регистрации
    # одного и того же физического аутентификатора.
    existing_creds = user.webauthn_credentials.all()
    exclude = [
        PublicKeyCredentialDescriptor(
            id=bytes(cred.credential_id),
            type=PublicKeyCredentialType.PUBLIC_KEY,
            transports=_parse_transports(cred.transports) or None,
        )
        for cred in existing_creds
    ]

    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        # user_id — bytes, идентифицирует пользователя для аутентификатора
        # НЕ должен содержать PII (используем числовой id, не email)
        user_id=str(user.id).encode('utf-8'),
        user_name=user.email,
        user_display_name=user.name,
        # attestation=NONE — не запрашиваем attestation statement (для приватности).
        # "None" означает: доверяем любому аутентификатору без проверки его модели.
        attestation=AttestationConveyancePreference.NONE,
        supported_pub_key_algs=SUPPORTED_ALGORITHMS,
        timeout=CEREMONY_TIMEOUT_MS,
        exclude_credentials=exclude,
        authenticator_selection=AuthenticatorSelectionCriteria(
            # PREFERRED — просим выполнить верификацию пользователя (PIN/биометрия),
            # но не блокируем USB-ключи без PIN
            user_verification=UserVerificationRequirement.PREFERRED,
            # PREFERRED resident key — позволяет discoverable credentials
            # (вход без ввода email)
            resident_key=ResidentKeyRequirement.PREFERRED,
        ),
    )

    # Сохраняем challenge и user_id в кэш для верификации на шаге 2
    session_id = _make_session_id()
    cache.set(
        f'passkey_reg:{session_id}',
        {
            'challenge': bytes_to_base64url(options.challenge),
            'user_id': user.id,
        },
        timeout=CHALLENGE_TTL,
    )

    logger.info('WebAuthn registration begin: user=%s session=%s', user.email, session_id)

    return {
        'options': json.loads(options_to_json(options)),
        'session_id': session_id,
    }


def complete_registration(
    user: User,
    session_id: str,
    credential_data: dict[str, Any],
    name: str = 'Мой Passkey',
) -> WebAuthnCredential:
    """
    Шаг 2 регистрации: верифицирует ответ аутентификатора и сохраняет ключ.

    Что проверяется (по спецификации WebAuthn Level 3):
    - Подпись clientDataJSON
    - rpIdHash совпадает с SHA-256(RP_ID)
    - origin совпадает с EXPECTED_ORIGIN
    - challenge совпадает с сохранённым (одноразовый)
    - Алгоритм подписи входит в SUPPORTED_ALGORITHMS

    Args:
        user: аутентифицированный пользователь
        session_id: ключ из кэша, полученный на шаге begin
        credential_data: JSON от navigator.credentials.create()
        name: человекочитаемое название ключа ("Ноут Windows", "iPhone" и т.д.)

    Returns:
        WebAuthnCredential — сохранённый объект

    Raises:
        ValueError: при любой ошибке верификации
    """
    # Получаем challenge из кэша и сразу удаляем (одноразовый!)
    session = cache.get(f'passkey_reg:{session_id}')
    if not session:
        raise ValueError('Сессия устарела или не найдена. Начните процесс регистрации заново.')

    if session['user_id'] != user.id:
        raise ValueError('Сессия принадлежит другому пользователю.')

    cache.delete(f'passkey_reg:{session_id}')
    expected_challenge = base64url_to_bytes(session['challenge'])

    # Извлекаем транспорты из ответа браузера
    raw_transports: list[str] = credential_data.get('response', {}).get('transports', [])
    parsed_transports = _parse_transports(raw_transports)

    # Строим объект RegistrationCredential для py_webauthn
    reg_credential = RegistrationCredential(
        id=credential_data['id'],
        raw_id=base64url_to_bytes(credential_data['rawId']),
        response=AuthenticatorAttestationResponse(
            client_data_json=base64url_to_bytes(
                credential_data['response']['clientDataJSON']
            ),
            attestation_object=base64url_to_bytes(
                credential_data['response']['attestationObject']
            ),
            # transports нужен для хранения, но не для верификации
            transports=parsed_transports if parsed_transports else None,
        ),
        type=credential_data.get('type', 'public-key'),
    )

    # Верификация: проверяем подпись, origin, rpIdHash, challenge
    verification = verify_registration_response(
        credential=reg_credential,
        expected_challenge=expected_challenge,
        expected_rp_id=RP_ID,
        expected_origin=EXPECTED_ORIGIN,
        # require_user_verification=False — не блокируем USB-ключи без PIN
        require_user_verification=False,
        supported_pub_key_algs=SUPPORTED_ALGORITHMS,
    )

    # Определяем тип устройства по транспортам
    device_type = _detect_device_type(raw_transports)

    # Сохраняем credential в базу данных
    cred = WebAuthnCredential.objects.create(
        user=user,
        credential_id=verification.credential_id,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        transports=raw_transports,
        name=name[:100],  # обрезаем до max_length модели
        device_type=device_type,
        backed_up=verification.credential_backed_up,
    )

    logger.info(
        'WebAuthn registration complete: user=%s device_type=%s backed_up=%s',
        user.email, device_type, verification.credential_backed_up,
    )

    return cred


# ────────────────────────────────────────────────────────────────────────────────
# ВХОД ЧЕРЕЗ PASSKEY
# ────────────────────────────────────────────────────────────────────────────────

def begin_login(email: str | None = None) -> dict[str, Any]:
    """
    Шаг 1 входа: генерирует PublicKeyCredentialRequestOptions.

    Поддерживает два режима:
    A) С email → передаём allowCredentials с ключами конкретного пользователя.
       Браузер сразу предложит нужный ключ.
    B) Без email → allowCredentials пустой → discoverable credentials.
       Браузер показывает общий пикер (Windows Hello выбирает аккаунт).

    Returns:
        {'options': dict, 'session_id': str}
    """
    allow_credentials: list[PublicKeyCredentialDescriptor] = []
    user_id_to_store: int | None = None

    if email:
        email = email.strip().lower()
        try:
            target_user = User.objects.get(email=email)
            user_id_to_store = target_user.id
            credentials = target_user.webauthn_credentials.all()
            allow_credentials = [
                PublicKeyCredentialDescriptor(
                    id=bytes(cred.credential_id),
                    type=PublicKeyCredentialType.PUBLIC_KEY,
                    transports=_parse_transports(cred.transports) or None,
                )
                for cred in credentials
            ]
        except User.DoesNotExist:
            # Не раскрываем существование аккаунта — просто продолжаем
            # без allowCredentials (discoverable flow)
            pass

    options = generate_authentication_options(
        rp_id=RP_ID,
        timeout=CEREMONY_TIMEOUT_MS,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    session_id = _make_session_id()
    cache.set(
        f'passkey_login:{session_id}',
        {
            'challenge': bytes_to_base64url(options.challenge),
            'user_id': user_id_to_store,  # None при discoverable flow
        },
        timeout=CHALLENGE_TTL,
    )

    logger.info('WebAuthn login begin: email=%s session=%s', email, session_id)

    return {
        'options': json.loads(options_to_json(options)),
        'session_id': session_id,
    }


def complete_login(
    session_id: str,
    credential_data: dict[str, Any],
    ip: str,
    user_agent: str,
) -> User:
    """
    Шаг 2 входа: верифицирует подпись и возвращает аутентифицированного пользователя.

    Проверки безопасности:
    1. challenge совпадает с сохранённым (одноразовый, TTL 5 мин)
    2. rpIdHash = SHA-256("localhost")
    3. origin = "http://localhost:3000"
    4. Подпись верифицируется публичным ключом из БД
    5. sign_count > сохранённого (защита от клонирования ключа)

    Args:
        session_id: из кэша, получен на шаге begin
        credential_data: JSON от navigator.credentials.get()
        ip: IP-адрес клиента (для аудит-лога)
        user_agent: User-Agent браузера (для аудит-лога)

    Returns:
        User — аутентифицированный пользователь

    Raises:
        ValueError: при любой ошибке верификации
    """
    # Получаем и удаляем challenge из кэша (одноразовый!)
    session = cache.get(f'passkey_login:{session_id}')
    if not session:
        raise ValueError('Сессия устарела. Начните вход заново.')
    cache.delete(f'passkey_login:{session_id}')

    expected_challenge = base64url_to_bytes(session['challenge'])
    stored_user_id: int | None = session.get('user_id')

    # Находим credential по rawId (бинарный идентификатор)
    try:
        credential_id_bytes = base64url_to_bytes(credential_data['rawId'])
        cred = WebAuthnCredential.objects.select_related('user').get(
            credential_id=credential_id_bytes
        )
    except WebAuthnCredential.DoesNotExist:
        _log_failure(None, ip, user_agent, 'Passkey не найден в базе данных')
        raise ValueError('Passkey не найден. Возможно, он был удалён.')

    authenticated_user = cred.user

    # Если сессия создана для конкретного пользователя — проверяем совпадение
    if stored_user_id is not None and stored_user_id != authenticated_user.id:
        _log_failure(authenticated_user, ip, user_agent, 'user_id mismatch')
        raise ValueError('Passkey не принадлежит данному пользователю.')

    # Обрабатываем userHandle (для discoverable credentials flow)
    raw_user_handle: str | None = credential_data.get('response', {}).get('userHandle')
    user_handle_bytes: bytes | None = None
    if raw_user_handle:
        user_handle_bytes = base64url_to_bytes(raw_user_handle)
        # Дополнительная проверка: userHandle должен совпадать с user.id
        expected_handle = str(authenticated_user.id).encode('utf-8')
        if user_handle_bytes != expected_handle:
            _log_failure(authenticated_user, ip, user_agent, 'userHandle mismatch')
            raise ValueError('Идентификатор пользователя не совпадает.')

    # Строим объект AuthenticationCredential для py_webauthn
    auth_credential = AuthenticationCredential(
        id=credential_data['id'],
        raw_id=credential_id_bytes,
        response=AuthenticatorAssertionResponse(
            client_data_json=base64url_to_bytes(
                credential_data['response']['clientDataJSON']
            ),
            authenticator_data=base64url_to_bytes(
                credential_data['response']['authenticatorData']
            ),
            signature=base64url_to_bytes(
                credential_data['response']['signature']
            ),
            user_handle=user_handle_bytes,
        ),
        type=credential_data.get('type', 'public-key'),
    )

    # Верификация подписи
    try:
        verification = verify_authentication_response(
            credential=auth_credential,
            expected_challenge=expected_challenge,
            expected_rp_id=RP_ID,
            expected_origin=EXPECTED_ORIGIN,
            # Публичный ключ из БД (bytes, не memoryview)
            credential_public_key=bytes(cred.public_key),
            credential_current_sign_count=cred.sign_count,
            require_user_verification=False,
        )
    except Exception as exc:
        error_msg = str(exc)
        # Определяем тип инцидента: replay/clone или обычная ошибка верификации
        is_clone_attack = any(kw in error_msg.lower() for kw in ['sign count', 'clone', 'replay'])
        if is_clone_attack:
            logger.critical(
                'SECURITY INCIDENT: Possible passkey clone! user=%s credential_id=%s ip=%s',
                authenticated_user.email,
                bytes_to_base64url(credential_id_bytes),
                ip,
            )
        _log_failure(authenticated_user, ip, user_agent, error_msg[:500])
        raise ValueError(f'Верификация подписи не прошла: {error_msg}')

    # Дополнительная проверка sign_count (защита от клонирования ключа).
    # Если оба счётчика ненулевые и новый НЕ больше старого — ключ, возможно, клонирован.
    # sign_count == 0 означает, что аутентификатор не поддерживает счётчики (некоторые платформы).
    new_count = verification.new_sign_count
    old_count = cred.sign_count
    if new_count > 0 and old_count > 0 and new_count <= old_count:
        logger.critical(
            'SECURITY INCIDENT: sign_count replay attack! '
            'user=%s old_count=%d new_count=%d ip=%s',
            authenticated_user.email, old_count, new_count, ip,
        )
        _log_failure(
            authenticated_user, ip, user_agent,
            f'sign_count replay: stored={old_count}, received={new_count}',
        )
        raise ValueError(
            'Обнаружена подозрительная активность (счётчик подписей). '
            'Ключ заблокирован. Обратитесь в поддержку.'
        )

    # Обновляем счётчик и время последнего использования
    cred.sign_count = new_count
    cred.last_used_at = timezone.now()
    cred.save(update_fields=['sign_count', 'last_used_at'])

    # Записываем успешный вход в журнал
    PasskeyLoginLog.objects.create(
        user=authenticated_user,
        ip=ip,
        user_agent=user_agent,
        success=True,
    )

    logger.info(
        'WebAuthn login success: user=%s device=%s ip=%s',
        authenticated_user.email, cred.name, ip,
    )

    return authenticated_user


def _log_failure(
    user: User | None,
    ip: str,
    user_agent: str,
    error_message: str,
) -> None:
    """Записывает неудачную попытку входа в журнал аудита."""
    PasskeyLoginLog.objects.create(
        user=user,
        ip=ip,
        user_agent=user_agent,
        success=False,
        error_message=error_message,
    )
    logger.warning(
        'WebAuthn login failure: user=%s ip=%s error=%s',
        user.email if user else 'unknown', ip, error_message,
    )
