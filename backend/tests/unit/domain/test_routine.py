"""Unit tests for the ``Routine`` domain entity.

These tests use only the Python standard library and the domain layer. They do
not import PostgreSQL, psycopg, FastAPI or any infrastructure module."""

from __future__ import annotations

import unittest
from datetime import date, datetime

from app.domain.entities.routine import Routine, RoutineStatus
from app.domain.exceptions.domain_exceptions import (
    InvalidDomainValue,
    InvalidRoutineReference,
    InvalidRoutineStateTransition,
)


def build_routine(**overrides: object) -> Routine:
    """Create a valid routine, overriding only the fields relevant to a test."""
    values: dict[str, object] = {
        "id_workout_program": 10,
        "id_trainer_creator": 20,
    }
    values.update(overrides)
    return Routine(**values)  # type: ignore[arg-type]


class RoutineCreationTests(unittest.TestCase):
    def test_valid_routine_uses_expected_defaults(self) -> None:
        routine = build_routine()

        self.assertIsNone(routine.id_routine)
        self.assertEqual(routine.status, RoutineStatus.DRAFT)
        self.assertIsInstance(routine.creation_date, date)
        self.assertIsNone(routine.id_client)
        self.assertIsNone(routine.id_routine_origin)

    def test_status_accepts_enum_members_and_strings(self) -> None:
        by_enum = build_routine(status=RoutineStatus.APPROVED)
        by_string = build_routine(status="APPROVED")

        self.assertEqual(by_enum.status, RoutineStatus.APPROVED)
        self.assertEqual(by_string.status, RoutineStatus.APPROVED)

    def test_invalid_status_is_rejected(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            build_routine(status="ARCHIVED")

    def test_program_and_trainer_identifiers_must_be_positive_integers(self) -> None:
        for value in (0, -1, True, "10", 1.5):
            with self.subTest(field="id_workout_program", value=value):
                with self.assertRaises(InvalidDomainValue):
                    build_routine(id_workout_program=value)

            with self.subTest(field="id_trainer_creator", value=value):
                with self.assertRaises(InvalidDomainValue):
                    build_routine(id_trainer_creator=value)

    def test_creation_date_must_be_a_date_not_a_datetime(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            build_routine(creation_date=datetime(2026, 1, 1, 12, 0))

    def test_optional_identifiers_must_be_positive_when_present(self) -> None:
        for value in (0, -1, True, "5"):
            with self.subTest(field="id_routine", value=value):
                with self.assertRaises(InvalidDomainValue):
                    build_routine(id_routine=value)

            with self.subTest(field="id_client", value=value):
                with self.assertRaises(InvalidDomainValue):
                    build_routine(id_client=value)

            with self.subTest(field="id_routine_origin", value=value):
                with self.assertRaises(InvalidDomainValue):
                    build_routine(id_routine_origin=value)

    def test_routine_cannot_be_its_own_origin_at_creation(self) -> None:
        with self.assertRaises(InvalidRoutineReference):
            build_routine(id_routine=7, id_routine_origin=7)


class RoutineOriginTests(unittest.TestCase):
    def test_set_origin_rejects_the_routine_itself(self) -> None:
        routine = build_routine(id_routine=7)

        with self.assertRaises(InvalidRoutineReference):
            routine.set_origin(7)

    def test_set_origin_requires_a_positive_identifier(self) -> None:
        routine = build_routine(id_routine=7)

        with self.assertRaises(InvalidDomainValue):
            routine.set_origin(0)

    def test_set_and_clear_origin(self) -> None:
        routine = build_routine(id_routine=7)

        routine.set_origin(3)
        self.assertEqual(routine.id_routine_origin, 3)

        routine.clear_origin()
        self.assertIsNone(routine.id_routine_origin)


class RoutineLifecycleTests(unittest.TestCase):
    def test_draft_can_be_submitted_for_review(self) -> None:
        routine = build_routine()

        routine.submit_for_review()

        self.assertEqual(routine.status, RoutineStatus.PENDING_REVIEW)

    def test_pending_review_can_be_approved(self) -> None:
        routine = build_routine(status=RoutineStatus.PENDING_REVIEW)

        routine.approve()

        self.assertEqual(routine.status, RoutineStatus.APPROVED)

    def test_pending_review_can_be_rejected(self) -> None:
        routine = build_routine(status=RoutineStatus.PENDING_REVIEW)

        routine.reject()

        self.assertEqual(routine.status, RoutineStatus.REJECTED)

    def test_rejected_routine_can_be_resubmitted(self) -> None:
        routine = build_routine(status=RoutineStatus.REJECTED)

        routine.resubmit_for_review()

        self.assertEqual(routine.status, RoutineStatus.PENDING_REVIEW)

    def test_invalid_transitions_are_rejected(self) -> None:
        draft = build_routine()
        with self.assertRaises(InvalidRoutineStateTransition):
            draft.approve()

        approved = build_routine(status=RoutineStatus.APPROVED)
        with self.assertRaises(InvalidRoutineStateTransition):
            approved.submit_for_review()

        rejected = build_routine(status=RoutineStatus.REJECTED)
        with self.assertRaises(InvalidRoutineStateTransition):
            rejected.approve()

    def test_can_transition_to_reports_allowed_targets(self) -> None:
        draft = build_routine()
        self.assertTrue(draft.can_transition_to(RoutineStatus.PENDING_REVIEW))
        self.assertTrue(draft.can_transition_to("PENDING_REVIEW"))
        self.assertFalse(draft.can_transition_to(RoutineStatus.APPROVED))

        pending = build_routine(status=RoutineStatus.PENDING_REVIEW)
        self.assertTrue(pending.can_transition_to(RoutineStatus.APPROVED))
        self.assertTrue(pending.can_transition_to(RoutineStatus.REJECTED))
        self.assertFalse(pending.can_transition_to(RoutineStatus.PENDING_REVIEW))

    def test_invalid_transition_target_is_rejected(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            build_routine().can_transition_to("ARCHIVED")

    def test_only_draft_and_rejected_routines_can_be_edited(self) -> None:
        self.assertTrue(build_routine().can_be_edited())
        self.assertTrue(build_routine(status=RoutineStatus.REJECTED).can_be_edited())
        self.assertFalse(
            build_routine(status=RoutineStatus.PENDING_REVIEW).can_be_edited()
        )
        self.assertFalse(build_routine(status=RoutineStatus.APPROVED).can_be_edited())

    def test_state_queries_match_current_status(self) -> None:
        cases = (
            (RoutineStatus.DRAFT, "is_draft"),
            (RoutineStatus.PENDING_REVIEW, "is_pending_review"),
            (RoutineStatus.APPROVED, "is_approved"),
            (RoutineStatus.REJECTED, "is_rejected"),
        )

        for status, method_name in cases:
            with self.subTest(status=status):
                routine = build_routine(status=status)
                self.assertTrue(getattr(routine, method_name)())

                for other_status, other_method in cases:
                    if other_status is not status:
                        self.assertFalse(getattr(routine, other_method)())


if __name__ == "__main__":
    unittest.main()