import uuid
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import TestCase

from users.models import PasskeyLoginLog, User, WebAuthnCredential
from users.services import webauthn as svc


def _make_user(email="test@edu.kz", name="Test"):
    return User.objects.create_user(email=email, name=name, password="pass1234")


class BeginRegistrationTest(TestCase):

    def test_returns_options_and_session_id(self):
        user = _make_user()
        result = svc.begin_registration(user)
        self.assertIn("options", result)
        self.assertIn("session_id", result)
        self.assertEqual(len(result["session_id"]), 32)

    def test_challenge_saved_to_cache(self):
        user = _make_user(email="a@edu.kz")
        result = svc.begin_registration(user)
        cached = cache.get(f"passkey_reg:{result['session_id']}")
        self.assertIsNotNone(cached)
        self.assertEqual(cached["user_id"], user.id)
        self.assertIn("challenge", cached)

    def test_existing_credentials_in_exclude_list(self):
        user = _make_user(email="b@edu.kz")
        WebAuthnCredential.objects.create(
            user=user,
            credential_id=b"existing-cred-id",
            public_key=b"pubkey",
            sign_count=0,
            transports=["internal"],
        )
        result = svc.begin_registration(user)
        excluded = result["options"].get("excludeCredentials", [])
        self.assertGreater(len(excluded), 0)


class BeginLoginTest(TestCase):

    def test_discoverable_flow_empty_allow_credentials(self):
        result = svc.begin_login(email=None)
        self.assertEqual(result["options"].get("allowCredentials", []), [])

    def test_known_email_fills_allow_credentials(self):
        user = _make_user(email="c@edu.kz")
        WebAuthnCredential.objects.create(
            user=user,
            credential_id=b"cred-c",
            public_key=b"pk-c",
            sign_count=0,
            transports=["internal"],
        )
        result = svc.begin_login(email="c@edu.kz")
        self.assertEqual(len(result["options"].get("allowCredentials", [])), 1)

    def test_unknown_email_treated_as_discoverable(self):
        result = svc.begin_login(email="nobody@edu.kz")
        self.assertEqual(result["options"].get("allowCredentials", []), [])


class SessionExpiryTest(TestCase):

    def test_missing_session_raises_value_error(self):
        with self.assertRaises(ValueError):
            svc.complete_login(
                session_id="no-such-session",
                credential_data={
                    "rawId": "aGVsbG8=",
                    "id": "aGVsbG8=",
                    "type": "public-key",
                    "response": {},
                },
                ip="127.0.0.1",
                user_agent="pytest",
            )


class SignCountReplayTest(TestCase):

    def _make_cred(self, user, sign_count=10):
        return WebAuthnCredential.objects.create(
            user=user,
            credential_id=uuid.uuid4().bytes,
            public_key=b"pubkey",
            sign_count=sign_count,
            transports=["internal"],
        )

    def test_lower_sign_count_raises_and_logs_failure(self):
        user = _make_user(email="replay@edu.kz")
        cred = self._make_cred(user, sign_count=10)

        from webauthn.helpers import bytes_to_base64url

        sid = "replay-test-001"
        cache.set(
            f"passkey_login:{sid}",
            {"challenge": bytes_to_base64url(b"r" * 32), "user_id": user.id},
            timeout=300,
        )
        raw_id = bytes_to_base64url(bytes(cred.credential_id))

        mock_ver = MagicMock()
        mock_ver.new_sign_count = 5  # сақталғаннан аз

        with patch(
            "users.services.webauthn.verify_authentication_response",
            return_value=mock_ver,
        ):
            with self.assertRaises(ValueError):
                svc.complete_login(
                    session_id=sid,
                    credential_data={
                        "rawId": raw_id,
                        "id": raw_id,
                        "type": "public-key",
                        "response": {
                            "clientDataJSON": bytes_to_base64url(b"cd"),
                            "authenticatorData": bytes_to_base64url(b"\x00" * 37),
                            "signature": bytes_to_base64url(b"sig"),
                        },
                    },
                    ip="10.0.0.1",
                    user_agent="test-agent",
                )

        log = PasskeyLoginLog.objects.filter(success=False).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.ip, "10.0.0.1")
