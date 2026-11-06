"""Unit tests for the variable routine structure (JSONB block tree).

The tests validate block-level rules, hierarchy rules, tree queries and JSON
serialization. No database connection or web framework is involved."""

from __future__ import annotations

import json
import unittest

from app.domain.entities.routine_structure import (
    BlockType,
    MAX_DEPTH,
    RoutineBlock,
    RoutineStructure,
)
from app.domain.exceptions.domain_exceptions import (
    InvalidDomainValue,
    InvalidStructure,
    StructureNotJsonSerializable,
)


def build_block(
    block_type: BlockType | str = BlockType.WARM_UP,
    order: int = 1,
    **overrides: object,
) -> RoutineBlock:
    """Create a block, overriding only the fields relevant to a test."""
    values: dict[str, object] = {
        "block_type": block_type,
        "order": order,
    }
    values.update(overrides)
    return RoutineBlock(**values)  # type: ignore[arg-type]


def nested_warm_up(depth: int) -> RoutineBlock:
    """Return a valid chain of WARM_UP blocks with the requested depth."""
    block = build_block()
    for _ in range(depth - 1):
        block = build_block(children=[block])
    return block


class RoutineBlockValidationTests(unittest.TestCase):
    def test_block_type_accepts_enum_members_and_strings(self) -> None:
        by_enum = build_block(block_type=BlockType.REST, rest_seconds=30)
        by_string = build_block(block_type="REST", rest_seconds=30)

        self.assertEqual(by_enum.block_type, BlockType.REST)
        self.assertEqual(by_string.block_type, BlockType.REST)

    def test_invalid_block_type_is_rejected(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            build_block(block_type="SPRINT")

    def test_exercise_and_set_blocks_require_an_exercise_reference(self) -> None:
        with self.assertRaises(InvalidStructure):
            build_block(block_type=BlockType.EXERCISE)

        with self.assertRaises(InvalidStructure):
            build_block(block_type=BlockType.SET, sets=3, repetitions=10)

    def test_set_blocks_require_sets_and_repetitions(self) -> None:
        with self.assertRaises(InvalidStructure):
            build_block(block_type=BlockType.SET, id_exercise=1)

        with self.assertRaises(InvalidStructure):
            build_block(
                block_type=BlockType.SET,
                id_exercise=1,
                sets=3,
            )

        valid = build_block(
            block_type=BlockType.SET,
            id_exercise=1,
            sets=3,
            repetitions=10,
        )
        self.assertEqual(valid.sets, 3)
        self.assertEqual(valid.repetitions, 10)

    def test_rest_blocks_require_a_duration_or_rest_time(self) -> None:
        with self.assertRaises(InvalidStructure):
            build_block(block_type=BlockType.REST)

        by_duration = build_block(block_type=BlockType.REST, duration_seconds=30)
        by_rest = build_block(block_type=BlockType.REST, rest_seconds=0)

        self.assertEqual(by_duration.duration_seconds, 30)
        self.assertEqual(by_rest.rest_seconds, 0)

    def test_order_must_be_a_positive_integer(self) -> None:
        for value in (0, -1, True, "1"):
            with self.subTest(value=value):
                with self.assertRaises(InvalidDomainValue):
                    build_block(order=value)

    def test_numeric_fields_validate_their_ranges(self) -> None:
        invalid_cases = (
            ("id_exercise", 0),
            ("sets", 0),
            ("repetitions", 0),
            ("duration_seconds", 0),
            ("rest_seconds", -1),
        )

        for field_name, value in invalid_cases:
            with self.subTest(field=field_name, value=value):
                with self.assertRaises(InvalidDomainValue):
                    build_block(**{field_name: value})

    def test_zero_rest_seconds_is_valid(self) -> None:
        block = build_block(rest_seconds=0)

        self.assertEqual(block.rest_seconds, 0)

    def test_notes_are_trimmed_and_blank_notes_become_none(self) -> None:
        trimmed = build_block(notes="  Keep the back straight  ")
        blank = build_block(notes="   ")
        missing = build_block(notes=None)

        self.assertEqual(trimmed.notes, "Keep the back straight")
        self.assertIsNone(blank.notes)
        self.assertIsNone(missing.notes)

    def test_notes_must_be_text_or_none(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            build_block(notes=123)

    def test_children_must_be_a_list_of_blocks(self) -> None:
        with self.assertRaises(InvalidStructure):
            build_block(children=())

        with self.assertRaises(InvalidStructure):
            build_block(children=[object()])

    def test_duplicate_child_orders_are_rejected(self) -> None:
        with self.assertRaises(InvalidStructure):
            build_block(
                children=[
                    build_block(BlockType.EXERCISE, 1, id_exercise=10),
                    build_block(BlockType.EXERCISE, 1, id_exercise=11),
                ]
            )

    def test_children_are_sorted_by_order(self) -> None:
        parent = build_block(
            children=[
                build_block(BlockType.EXERCISE, 2, id_exercise=20),
                build_block(BlockType.EXERCISE, 1, id_exercise=10),
            ]
        )

        self.assertEqual([child.order for child in parent.children], [1, 2])


class RoutineStructureValidationTests(unittest.TestCase):
    def test_valid_structure_sorts_root_blocks(self) -> None:
        late = build_block(order=2)
        early = build_block(order=1)

        structure = RoutineStructure(id_routine=5, blocks=[late, early])

        self.assertEqual([block.order for block in structure.blocks], [1, 2])

    def test_structure_requires_a_positive_routine_identifier(self) -> None:
        for value in (0, -1, True, "5"):
            with self.subTest(value=value):
                with self.assertRaises(InvalidDomainValue):
                    RoutineStructure(id_routine=value)

    def test_root_blocks_must_be_a_list_of_blocks(self) -> None:
        with self.assertRaises(InvalidStructure):
            RoutineStructure(id_routine=1, blocks=())

        with self.assertRaises(InvalidStructure):
            RoutineStructure(id_routine=1, blocks=[object()])

    def test_duplicate_root_orders_are_rejected(self) -> None:
        with self.assertRaises(InvalidStructure):
            RoutineStructure(
                id_routine=1,
                blocks=[build_block(order=1), build_block(order=1)],
            )

    def test_empty_structure_is_reported_as_empty(self) -> None:
        structure = RoutineStructure(id_routine=1)

        self.assertTrue(structure.is_empty())
        self.assertEqual(structure.depth(), 0)
        self.assertEqual(list(structure.walk()), [])

    def test_structure_depth_limit_is_enforced(self) -> None:
        allowed = RoutineStructure(
            id_routine=1,
            blocks=[nested_warm_up(MAX_DEPTH)],
        )
        self.assertEqual(allowed.depth(), MAX_DEPTH)

        with self.assertRaises(InvalidStructure):
            RoutineStructure(
                id_routine=1,
                blocks=[nested_warm_up(MAX_DEPTH + 1)],
            )

    def test_tree_queries_return_exercises_sets_and_depth(self) -> None:
        structure = RoutineStructure(
            id_routine=1,
            blocks=[
                build_block(
                    order=1,
                    children=[
                        build_block(
                            BlockType.SET,
                            order=1,
                            id_exercise=10,
                            sets=3,
                            repetitions=12,
                        ),
                        build_block(
                            BlockType.SET,
                            order=2,
                            id_exercise=11,
                            sets=4,
                            repetitions=10,
                        ),
                    ],
                ),
                build_block(BlockType.EXERCISE, order=2, id_exercise=10),
            ],
        )

        self.assertFalse(structure.is_empty())
        self.assertEqual(structure.depth(), 2)
        self.assertEqual(structure.referenced_exercise_ids(), {10, 11})
        self.assertEqual(structure.total_sets(), 7)
        self.assertEqual([block.order for block in structure.walk()], [1, 1, 2, 2])


class RoutineStructureSerializationTests(unittest.TestCase):
    def build_structure(self) -> RoutineStructure:
        return RoutineStructure(
            id_routine=1,
            blocks=[
                build_block(
                    order=1,
                    notes="  Warm up  ",
                    children=[
                        build_block(
                            BlockType.SET,
                            order=1,
                            id_exercise=10,
                            sets=3,
                            repetitions=12,
                            rest_seconds=45,
                        )
                    ],
                )
            ],
        )

    def test_to_dict_and_from_dict_round_trip(self) -> None:
        structure = self.build_structure()
        data = structure.to_dict()

        restored = RoutineStructure.from_dict(1, data)

        self.assertEqual(restored.to_dict(), data)
        self.assertEqual(restored.total_sets(), structure.total_sets())

    def test_from_dict_accepts_a_block_list_or_an_object(self) -> None:
        block_data = {"block_type": "WARM_UP", "order": 1}

        from_list = RoutineStructure.from_dict(1, [block_data])
        from_object = RoutineStructure.from_dict(1, {"blocks": [block_data]})

        self.assertEqual(from_list.to_dict(), from_object.to_dict())

    def test_from_dict_rejects_invalid_payloads(self) -> None:
        invalid_payloads = (
            "not-a-structure",
            123,
            {"blocks": "not-a-list"},
            [42],
            [{"order": 1}],
            [{"block_type": "WARM_UP", "order": 1, "children": "not-a-list"}],
        )

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(InvalidStructure):
                    RoutineStructure.from_dict(1, payload)  # type: ignore[arg-type]

    def test_jsonb_document_is_valid_json(self) -> None:
        structure = self.build_structure()

        serialized = structure.to_jsonb_document()

        self.assertEqual(json.loads(serialized), structure.to_dict())
        structure.ensure_json_compatible()

    def test_non_serializable_values_raise_a_domain_error(self) -> None:
        structure = self.build_structure()
        structure.blocks[0].notes = object()  # type: ignore[assignment]

        with self.assertRaises(StructureNotJsonSerializable):
            structure.to_jsonb_document()


if __name__ == "__main__":
    unittest.main()