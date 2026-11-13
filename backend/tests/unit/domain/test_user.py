"""Unit tests for the User domain entity."""

import unittest

from app.domain.entities.user import User
from app.domain.value_objects.user_role import UserRole


class UserTests(unittest.TestCase):
    def test_accepts_a_persisted_role_and_exposes_role_checks(self) -> None:
        user = User(
            name="Alex Cuervo",
            email="alex@example.com",
            password_hash="hashed-password",
            role="trainer",
            id_user=1,
        )

        self.assertIs(user.role, UserRole.TRAINER)
        self.assertTrue(user.is_trainer())
        self.assertFalse(user.is_admin())
        self.assertFalse(user.is_client())
        self.assertTrue(user.active)

    def test_rejects_empty_name(self) -> None:
        with self.assertRaises(ValueError):
            User("", "alex@example.com", "hashed-password", UserRole.CLIENT)

    def test_rejects_invalid_email(self) -> None:
        with self.assertRaises(ValueError):
            User("Alex Cuervo", "invalid-email", "hashed-password", UserRole.CLIENT)

    def test_rejects_inactive_status_with_a_non_boolean_value(self) -> None:
        with self.assertRaises(ValueError):
            User(
                "Alex Cuervo",
                "alex@example.com",
                "hashed-password",
                UserRole.CLIENT,
                active=1,
            )


if __name__ == "__main__":
    unittest.main()
