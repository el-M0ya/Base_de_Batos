"""Unit tests for trainer authorization rules."""

import unittest
from datetime import date

from app.domain.entities.authorisation import Authorisation
from app.domain.exceptions.domain_exceptions import InvalidDateRange, InvalidDomainValue


class AuthorisationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authorization = Authorisation(
            id_trainer=10,
            id_workout_program=20,
            can_generate=True,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )

    def test_allows_generation_inside_its_active_period(self) -> None:
        self.assertTrue(
            self.authorization.is_generation_authorized(date(2026, 6, 15))
        )
        self.assertFalse(
            self.authorization.is_generation_authorized(date(2027, 1, 1))
        )

    def test_does_not_allow_validation_without_validation_permission(self) -> None:
        self.assertFalse(
            self.authorization.is_validation_authorized(date(2026, 6, 15))
        )

    def test_combined_permissions_are_checked_independently(self) -> None:
        authorization = Authorisation(10, 20, True, True, date(2026, 1, 1))
        self.assertTrue(authorization.allows_generation_on(date(2026, 6, 1)))
        self.assertTrue(authorization.allows_validation_on(date(2026, 6, 1)))

    def test_not_yet_effective_authorization_grants_no_access(self) -> None:
        self.assertFalse(self.authorization.allows_generation_on(date(2025, 12, 31)))
        self.assertFalse(self.authorization.allows_validation_on(date(2025, 12, 31)))

    def test_open_ended_authorization_remains_effective(self) -> None:
        authorization = Authorisation(10, 20, can_validate=True, start_date=date(2026, 1, 1))
        self.assertTrue(authorization.allows_validation_on(date(2099, 1, 1)))

    def test_rejects_an_invalid_date_range(self) -> None:
        with self.assertRaises(InvalidDateRange):
            Authorisation(
                10,
                20,
                can_validate=True,
                start_date=date(2026, 6, 1),
                end_date=date(2026, 5, 31),
            )

    def test_rejects_authorization_without_permissions(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            Authorisation(10, 20)


if __name__ == "__main__":
    unittest.main()
