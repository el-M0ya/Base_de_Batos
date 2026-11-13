"""Unit tests for the ``Routine`` State pattern and lifecycle mapping."""

from __future__ import annotations

import unittest

from app.domain.entities.routine import Routine, RoutineStatus
from app.domain.exceptions.domain_exceptions import (
    InvalidDomainValue,
    InvalidRoutineStateTransition,
    RejectedValidationRequiresObservations,
)
from app.domain.states import (
    ApprovedState,
    DraftState,
    PendingReviewState,
    RejectedState,
    ReplacedState,
    persisted_value_for_state,
    state_for_status,
    state_from_persisted,
    status_for_state,
)


def build_routine(**overrides: object) -> Routine:
    values: dict[str, object] = {
        "id_workout_program": 10,
        "id_trainer_creator": 20,
    }
    values.update(overrides)
    return Routine(**values)  # type: ignore[arg-type]


class PersistedStatusMappingTests(unittest.TestCase):
    def test_every_domain_status_maps_to_a_state(self) -> None:
        cases = (
            (RoutineStatus.DRAFT, DraftState),
            (RoutineStatus.PENDING_REVIEW, PendingReviewState),
            (RoutineStatus.APPROVED, ApprovedState),
            (RoutineStatus.REJECTED, RejectedState),
            (RoutineStatus.REPLACED, ReplacedState),
        )

        for status, expected_state in cases:
            with self.subTest(status=status):
                self.assertIsInstance(state_for_status(status), expected_state)
                self.assertIsInstance(
                    state_from_persisted(status.value), expected_state
                )

    def test_state_status_round_trips_to_persisted_value(self) -> None:
        for status in RoutineStatus:
            with self.subTest(status=status):
                state = state_for_status(status)
                self.assertIs(status_for_state(state), status)
                self.assertEqual(persisted_value_for_state(state), status.value)

    def test_persisted_strings_are_normalised(self) -> None:
        self.assertIsInstance(
            state_for_status("  pending_review  "), PendingReviewState
        )

    def test_unknown_persisted_status_is_rejected(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            state_for_status("ARCHIVED")

    def test_non_text_status_is_rejected(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            state_for_status(1)

    def test_status_for_state_rejects_non_state_values(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            status_for_state("PENDING_REVIEW")  # type: ignore[arg-type]

    def test_routine_state_property_tracks_its_status(self) -> None:
        cases = (
            (RoutineStatus.DRAFT, DraftState),
            (RoutineStatus.PENDING_REVIEW, PendingReviewState),
            (RoutineStatus.APPROVED, ApprovedState),
            (RoutineStatus.REJECTED, RejectedState),
            (RoutineStatus.REPLACED, ReplacedState),
        )

        for status, expected_state in cases:
            with self.subTest(status=status):
                routine = build_routine(status=status)
                self.assertIsInstance(routine.state, expected_state)


class StateTransitionTests(unittest.TestCase):
    def test_draft_can_be_submitted(self) -> None:
        routine = build_routine()

        routine.submit_for_review()

        self.assertIsInstance(routine.state, PendingReviewState)

    def test_pending_review_can_be_approved(self) -> None:
        routine = build_routine(status=RoutineStatus.PENDING_REVIEW)

        routine.approve()

        self.assertIsInstance(routine.state, ApprovedState)

    def test_pending_review_can_be_rejected_with_observations(self) -> None:
        routine = build_routine(status=RoutineStatus.PENDING_REVIEW)

        routine.reject("The volume is too high for the client.")

        self.assertIsInstance(routine.state, RejectedState)

    def test_pending_review_can_be_replaced(self) -> None:
        routine = build_routine(status=RoutineStatus.PENDING_REVIEW)

        routine.replace()

        self.assertIsInstance(routine.state, ReplacedState)

    def test_rejected_routine_can_be_resubmitted(self) -> None:
        routine = build_routine(status=RoutineStatus.REJECTED)

        routine.resubmit_for_review()

        self.assertIsInstance(routine.state, PendingReviewState)

    def test_replacement_routine_keeps_the_source_reference(self) -> None:
        source = build_routine(id_routine=7, status=RoutineStatus.PENDING_REVIEW)

        source.replace()
        replacement = build_routine(id_routine=8, id_routine_origin=source.id_routine)

        self.assertIsInstance(source.state, ReplacedState)
        self.assertEqual(replacement.id_routine_origin, source.id_routine)

    def test_rejection_requires_non_empty_observations(self) -> None:
        routine = build_routine(status=RoutineStatus.PENDING_REVIEW)

        for observations in (None, "", "   "):
            with self.subTest(observations=observations):
                with self.assertRaises(RejectedValidationRequiresObservations):
                    routine.reject(observations)

        self.assertIsInstance(routine.state, PendingReviewState)

    def test_draft_cannot_transition_directly_to_other_states(self) -> None:
        for action in (
            lambda routine: routine.approve(),
            lambda routine: routine.reject("Reason"),
            lambda routine: routine.replace(),
        ):
            with self.subTest(action=action):
                routine = build_routine()
                with self.assertRaises(InvalidRoutineStateTransition):
                    action(routine)

    def test_pending_review_cannot_be_submitted_again(self) -> None:
        routine = build_routine(status=RoutineStatus.PENDING_REVIEW)

        with self.assertRaises(InvalidRoutineStateTransition):
            routine.submit_for_review()

    def test_approved_routine_is_terminal(self) -> None:
        actions = (
            lambda routine: routine.submit_for_review(),
            lambda routine: routine.resubmit_for_review(),
            lambda routine: routine.approve(),
            lambda routine: routine.reject("Reason"),
            lambda routine: routine.replace(),
        )

        for action in actions:
            with self.subTest(action=action):
                routine = build_routine(status=RoutineStatus.APPROVED)
                with self.assertRaises(InvalidRoutineStateTransition):
                    action(routine)

    def test_rejected_routine_cannot_be_approved_rejected_or_replaced(self) -> None:
        actions = (
            lambda routine: routine.approve(),
            lambda routine: routine.reject("Reason"),
            lambda routine: routine.replace(),
        )

        for action in actions:
            with self.subTest(action=action):
                routine = build_routine(status=RoutineStatus.REJECTED)
                with self.assertRaises(InvalidRoutineStateTransition):
                    action(routine)

    def test_replaced_routine_is_terminal(self) -> None:
        actions = (
            lambda routine: routine.submit_for_review(),
            lambda routine: routine.resubmit_for_review(),
            lambda routine: routine.approve(),
            lambda routine: routine.reject("Reason"),
            lambda routine: routine.replace(),
        )

        for action in actions:
            with self.subTest(action=action):
                routine = build_routine(status=RoutineStatus.REPLACED)
                with self.assertRaises(InvalidRoutineStateTransition):
                    action(routine)

    def test_can_transition_to_is_state_specific(self) -> None:
        pending = build_routine(status=RoutineStatus.PENDING_REVIEW)
        self.assertTrue(pending.can_transition_to(RoutineStatus.REPLACED))
        self.assertFalse(pending.can_transition_to(RoutineStatus.DRAFT))

        replaced = build_routine(status=RoutineStatus.REPLACED)
        self.assertFalse(replaced.can_transition_to(RoutineStatus.PENDING_REVIEW))


if __name__ == "__main__":
    unittest.main()
