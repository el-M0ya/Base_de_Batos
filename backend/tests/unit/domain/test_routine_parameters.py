"""Unit tests for the ``RoutineParameters`` domain entity.

The suite covers the generation-parameter invariants: valid ranges, ratio
bounds, completeness and muscle-group coverage. It does not use PostgreSQL or
any web framework."""

from __future__ import annotations

import unittest
from decimal import Decimal

from app.domain.entities.routine_parameters import (
    IntensityLevel,
    RoutineParameters,
)
from app.domain.exceptions.domain_exceptions import (
    InvalidDomainValue,
    InvalidParameters,
)


def build_parameters(**overrides: object) -> RoutineParameters:
    """Create valid generation parameters, overriding only the fields under test."""
    values: dict[str, object] = {
        "id_routine": 1,
        "total_exercises": 6,
        "intensity_level": IntensityLevel.MEDIUM,
        "cardio_ratio": Decimal("40"),
        "strength_ratio": Decimal("60"),
    }
    values.update(overrides)
    return RoutineParameters(**values)  # type: ignore[arg-type]


class RoutineParametersCreationTests(unittest.TestCase):
    def test_valid_parameters_are_complete(self) -> None:
        parameters = build_parameters()

        self.assertEqual(parameters.total_ratio(), Decimal("100"))
        self.assertEqual(parameters.remaining_ratio(), Decimal("0"))
        self.assertTrue(parameters.is_complete())

    def test_intensity_accepts_enum_members_and_strings(self) -> None:
        by_enum = build_parameters(intensity_level=IntensityLevel.HIGH)
        by_string = build_parameters(intensity_level="LOW")

        self.assertEqual(by_enum.intensity_level, IntensityLevel.HIGH)
        self.assertEqual(by_string.intensity_level, IntensityLevel.LOW)

    def test_invalid_intensity_is_rejected(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            build_parameters(intensity_level="EXTREME")

    def test_ratios_are_coerced_to_decimal(self) -> None:
        parameters = build_parameters(cardio_ratio="25", strength_ratio=75)

        self.assertEqual(parameters.cardio_ratio, Decimal("25"))
        self.assertEqual(parameters.strength_ratio, Decimal("75"))
        self.assertEqual(parameters.total_ratio(), Decimal("100"))

    def test_invalid_ratio_values_are_rejected(self) -> None:
        for value in (True, "not-a-number", object()):
            with self.subTest(value=value):
                with self.assertRaises(InvalidDomainValue):
                    build_parameters(cardio_ratio=value)

    def test_identifier_and_exercise_count_must_be_positive(self) -> None:
        for value in (0, -1, True, "6"):
            with self.subTest(field="id_routine", value=value):
                with self.assertRaises(InvalidDomainValue):
                    build_parameters(id_routine=value)

            with self.subTest(field="total_exercises", value=value):
                with self.assertRaises(InvalidDomainValue):
                    build_parameters(total_exercises=value)


class RoutineParametersRatioTests(unittest.TestCase):
    def test_ratios_cannot_be_negative(self) -> None:
        with self.assertRaises(InvalidParameters):
            build_parameters(cardio_ratio=Decimal("-1"))

    def test_a_single_ratio_cannot_exceed_one_hundred_percent(self) -> None:
        with self.assertRaises(InvalidParameters):
            build_parameters(cardio_ratio=Decimal("101"))

    def test_the_sum_of_ratios_cannot_exceed_one_hundred_percent(self) -> None:
        with self.assertRaises(InvalidParameters):
            build_parameters(
                cardio_ratio=Decimal("60"),
                strength_ratio=Decimal("50"),
            )

    def test_zero_ratios_are_valid_but_incomplete(self) -> None:
        parameters = build_parameters(
            cardio_ratio=Decimal("0"),
            strength_ratio=Decimal("0"),
        )

        self.assertEqual(parameters.remaining_ratio(), Decimal("100"))
        self.assertFalse(parameters.is_complete())

    def test_flexibility_ratio_participates_in_the_total(self) -> None:
        parameters = build_parameters(
            cardio_ratio=Decimal("40"),
            strength_ratio=Decimal("40"),
            flexibility_ratio=Decimal("20"),
        )

        self.assertEqual(parameters.total_ratio(), Decimal("100"))
        self.assertTrue(parameters.is_complete())

    def test_incomplete_parameters_report_the_remaining_ratio(self) -> None:
        parameters = build_parameters(
            cardio_ratio=Decimal("30"),
            strength_ratio=Decimal("20"),
        )

        self.assertEqual(parameters.remaining_ratio(), Decimal("50"))
        self.assertFalse(parameters.is_complete())


class RoutineParametersMuscleGroupTests(unittest.TestCase):
    def test_covered_muscle_groups_are_deduplicated_and_ordered(self) -> None:
        parameters = build_parameters(
            covered_muscle_group_ids=[3, 1, 3, 2, 1],
        )

        self.assertEqual(parameters.covered_muscle_group_ids, [3, 1, 2])

    def test_muscle_group_collection_accepts_supported_iterables(self) -> None:
        parameters = build_parameters(covered_muscle_group_ids=(2, 1, 2))

        self.assertEqual(parameters.covered_muscle_group_ids, [2, 1])

    def test_none_becomes_an_empty_muscle_group_list(self) -> None:
        parameters = build_parameters(covered_muscle_group_ids=None)

        self.assertEqual(parameters.covered_muscle_group_ids, [])

    def test_muscle_group_identifiers_must_be_positive_integers(self) -> None:
        for value in (0, -1, True, "2"):
            with self.subTest(value=value):
                with self.assertRaises(InvalidDomainValue):
                    build_parameters(covered_muscle_group_ids=[value])

    def test_muscle_group_collection_must_be_an_iterable_collection(self) -> None:
        for value in ("1,2", 123, object()):
            with self.subTest(value=value):
                with self.assertRaises(InvalidDomainValue):
                    build_parameters(covered_muscle_group_ids=value)

    def test_covers_checks_a_single_muscle_group(self) -> None:
        parameters = build_parameters(covered_muscle_group_ids=[1, 3])

        self.assertTrue(parameters.covers(1))
        self.assertFalse(parameters.covers(2))

    def test_covers_all_checks_the_whole_collection(self) -> None:
        parameters = build_parameters(covered_muscle_group_ids=[1, 2, 3])

        self.assertTrue(parameters.covers_all([1, 3]))
        self.assertTrue(parameters.covers_all([]))
        self.assertFalse(parameters.covers_all([1, 4]))

    def test_default_muscle_group_lists_are_independent(self) -> None:
        first = build_parameters()
        second = build_parameters()

        first.covered_muscle_group_ids.append(9)

        self.assertEqual(first.covered_muscle_group_ids, [9])
        self.assertEqual(second.covered_muscle_group_ids, [])


if __name__ == "__main__":
    unittest.main()