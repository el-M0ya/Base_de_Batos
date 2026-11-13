"""Unit tests for the concrete password and JWT adapters."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.application.exceptions import ExpiredToken, InvalidToken
from app.infrastructure.security.jwt_token_service import JwtTokenService
from app.infrastructure.security.password_hasher_bcrypt import BcryptPasswordHasher

_SECRET = "test-secret-key-with-at-least-32-characters"


class BcryptPasswordHasherTests(unittest.TestCase):
    def test_hash_is_not_plaintext_and_verify_works(self) -> None:
        hasher = BcryptPasswordHasher(rounds=10)

        hashed = hasher.hash("correct horse battery staple")

        self.assertNotEqual(hashed, "correct horse battery staple")
        self.assertTrue(hashed.startswith("$2"))
        self.assertTrue(hasher.verify("correct horse battery staple", hashed))
        self.assertFalse(hasher.verify("wrong password", hashed))

    def test_malformed_hash_is_a_failed_verification(self) -> None:
        hasher = BcryptPasswordHasher(rounds=10)

        self.assertFalse(hasher.verify("anything", "not-a-bcrypt-hash"))


class JwtTokenServiceTests(unittest.TestCase):
    def test_issue_and_decode_round_trip(self) -> None:
        service = JwtTokenService(_SECRET, expire_minutes=30)

        issued = service.issue(42)
        payload = service.decode(issued.token)

        self.assertEqual(payload.id_user, 42)
        self.assertGreater(payload.expires_at, datetime.now(timezone.utc))

    def test_non_expired_token_has_expected_subject(self) -> None:
        service = JwtTokenService(_SECRET, expire_minutes=30)
        issued = service.issue(7)

        payload = service.decode(issued.token)

        self.assertEqual(payload.id_user, 7)

    def test_expired_token_is_rejected(self) -> None:
        service = JwtTokenService(_SECRET, expire_minutes=30)
        token = jwt.encode(
            {
                "sub": "7",
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            _SECRET,
            algorithm="HS256",
        )

        with self.assertRaises(ExpiredToken):
            service.decode(token)

    def test_tampered_token_is_rejected(self) -> None:
        service = JwtTokenService(_SECRET, expire_minutes=30)
        issued = service.issue(7)

        with self.assertRaises(InvalidToken):
            service.decode(issued.token + "tampered")

    def test_token_signed_with_another_key_is_rejected(self) -> None:
        issuer = JwtTokenService("another-secret-key-with-at-least-32-characters")
        verifier = JwtTokenService(_SECRET)

        with self.assertRaises(InvalidToken):
            verifier.decode(issuer.issue(7).token)

    def test_token_without_subject_is_rejected(self) -> None:
        service = JwtTokenService(_SECRET)
        token = jwt.encode(
            {"exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
            _SECRET,
            algorithm="HS256",
        )

        with self.assertRaises(InvalidToken):
            service.decode(token)

    def test_short_secret_is_rejected_at_startup(self) -> None:
        with self.assertRaises(ValueError):
            JwtTokenService("too-short")
