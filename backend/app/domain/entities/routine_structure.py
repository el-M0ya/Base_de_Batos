"""Variable block structure of a routine (JSONB)"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator, Optional

from app.domain.exceptions.domain_exceptions import (
    InvalidDomainValue,
    InvalidStructure,
    StructureNotJsonSerializable,
)


class BlockType(str, Enum):
    WARM_UP = "WARM_UP"
    CIRCUIT = "CIRCUIT"
    SET = "SET"
    REST = "REST"
    EXERCISE = "EXERCISE"

MAX_DEPTH = 20

def _ensure_positive_int(value: object, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidDomainValue(field_name, value, "an integer greater than 0")

def _ensure_non_negative_int(value: object, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise InvalidDomainValue(field_name, value, "an integer greater or equal than 0")

@dataclass
class RoutineBlock:
    block_type: BlockType
    order: int
    id_exercise: Optional[int] = None
    sets: Optional[int] = None
    repetitions: Optional[int] = None
    rest_seconds: Optional[int] = None
    duration_seconds: Optional[int] = None
    notes: Optional[str] = None
    children: list["RoutineBlock"] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._validate_fields()
        self._validate_children_collection()
        self._sort_and_validate_children()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @staticmethod
    def _coerce_block_type(value: object) -> BlockType:
        if isinstance(value, BlockType):
            return value
        try:
            return BlockType(value)  # type: ignore[arg-type] 
        except ValueError as exc:
            raise InvalidDomainValue(
                "block_type", value, f"one of {[b.value for b in BlockType]}"
            ) from exc

    @staticmethod
    def _normalise_notes(value: object) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str):
            raise InvalidDomainValue("notes", value, "a text string or None")
        stripped = value.strip()
        return stripped or None

    def _validate_fields(self) -> None:
        self.block_type = self._coerce_block_type(self.block_type)
        self.notes = self._normalise_notes(self.notes)
        _ensure_positive_int(self.order, "order")

        if self.id_exercise is not None:
            _ensure_positive_int(self.id_exercise, "id_exercise")
        if self.sets is not None:
            _ensure_positive_int(self.sets, "sets")
        if self.repetitions is not None:
            _ensure_positive_int(self.repetitions, "repetitions")
        if self.rest_seconds is not None:
            _ensure_non_negative_int(self.rest_seconds, "rest_seconds")
        if self.duration_seconds is not None:
            _ensure_positive_int(self.duration_seconds, "duration_seconds")

        if self.block_type in (BlockType.EXERCISE, BlockType.SET):
            if self.id_exercise is None:
                raise InvalidStructure(
                    f"A block of '{self.block_type.value}' most reference an "
                    "exercise (id_exercise)."
                )

        if self.block_type is BlockType.REST:
            if self.duration_seconds is None and self.rest_seconds is None:
                raise InvalidStructure(
                    "A block of 'REST' must indicate duration_seconds or "
                    "rest_seconds."
                )

        if self.block_type is BlockType.SET:
            if self.sets is None or self.repetitions is None:
                raise InvalidStructure(
                    "A block of 'SET' must indicate sets and repetitions."
                )

    def _validate_children_collection(self) -> None:
        if not isinstance(self.children, list):
            raise InvalidStructure(
                "'children' must be a list of RoutineBlock."
            )
        for child in self.children:
            if not isinstance(child, RoutineBlock):
                raise InvalidStructure(
                    "All childrens must be an instance of  RoutineBlock."
                )

    def _sort_and_validate_children(self) -> None:
        orders = [child.order for child in self.children]
        if len(orders) != len(set(orders)):
            raise InvalidStructure(
                f"The structure exceeds the maximum depth of "
                f"{self.block_type.value} (order={self.order})."
            )
        self.children.sort(key=lambda child: child.order)

    def validate(self, level: int = 1) -> None:
        if level > MAX_DEPTH:
            raise InvalidStructure(
                f"The structure exceeds the maximum depth of {MAX_DEPTH}."
            )

        self._validate_fields()
        self._validate_children_collection()
        self._sort_and_validate_children()

        for child in self.children:
            child.validate(level + 1)

    # ------------------------------------------------------------------
    # Route
    # ------------------------------------------------------------------
    def walk(self) -> Iterator["RoutineBlock"]:
        yield self
        for child in self.children:
            yield from child.walk()

    def depth(self) -> int:
        if not self.children:
            return 1
        return 1 + max(child.depth() for child in self.children)

    def referenced_exercise_ids(self) -> set[int]:
        ids = {block.id_exercise for block in self.walk() if block.id_exercise}
        return {value for value in ids if value is not None}

    def total_sets(self) -> int:
        return sum(block.sets or 0 for block in self.walk())

    # ------------------------------------------------------------------
    # Serialization JSONB
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        data: dict = {
            "block_type": self.block_type.value,
            "order": self.order,
            "children": [child.to_dict() for child in self.children],
        }
        if self.id_exercise is not None:
            data["id_exercise"] = self.id_exercise
        if self.sets is not None:
            data["sets"] = self.sets
        if self.repetitions is not None:
            data["repetitions"] = self.repetitions
        if self.rest_seconds is not None:
            data["rest_seconds"] = self.rest_seconds
        if self.duration_seconds is not None:
            data["duration_seconds"] = self.duration_seconds
        if self.notes is not None:
            data["notes"] = self.notes
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "RoutineBlock":
        if not isinstance(data, dict):
            raise InvalidStructure("Each block has to be a JSON object.")

        children_data = data.get("children", [])
        if not isinstance(children_data, list):
            raise InvalidStructure("'children' has to be a list.")

        try:
            block_type = data["block_type"]
            order = data["order"]
        except KeyError as exc:
            raise InvalidStructure(
                f"Required field is missing {exc.args[0]!r} in a block."
            ) from exc

        return cls(
            block_type=block_type,
            order=order,
            id_exercise=data.get("id_exercise"),
            sets=data.get("sets"),
            repetitions=data.get("repetitions"),
            rest_seconds=data.get("rest_seconds"),
            duration_seconds=data.get("duration_seconds"),
            notes=data.get("notes"),
            children=[cls.from_dict(child) for child in children_data],
        )


@dataclass
class RoutineStructure:
    id_routine: int
    blocks: list[RoutineBlock] = field(default_factory=list)

    def __post_init__(self) -> None:
        _ensure_positive_int(self.id_routine, "id_routine")
        if not isinstance(self.blocks, list):
            raise InvalidStructure("'blocks' must be a list of RoutineBlock.")
        for block in self.blocks:
            if not isinstance(block, RoutineBlock):
                raise InvalidStructure(
                    "All root blocks must be instances of RoutineBlock."
                )
        self.validate()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate(self) -> None:
        orders = [block.order for block in self.blocks]
        if len(orders) != len(set(orders)):
            raise InvalidStructure(
                "There are duplicates orders in the routine's root blocks."
            )

        self.blocks.sort(key=lambda block: block.order)
        for block in self.blocks:
            block.validate(level=1)

    # ------------------------------------------------------------------
    # Consults
    # ------------------------------------------------------------------
    def is_empty(self) -> bool:
        return not self.blocks

    def referenced_exercise_ids(self) -> set[int]:
        ids: set[int] = set()
        for block in self.blocks:
            ids.update(block.referenced_exercise_ids())
        return ids

    def total_sets(self) -> int:
        return sum(block.total_sets() for block in self.blocks)

    def depth(self) -> int:
        if not self.blocks:
            return 0
        return max(block.depth() for block in self.blocks)

    def walk(self) -> Iterator[RoutineBlock]:
        for block in self.blocks:
            yield from block.walk()

    # ------------------------------------------------------------------
    # Serialization JSONB
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {"blocks": [block.to_dict() for block in self.blocks]}

    def to_jsonb_document(self) -> str:
        document = self.to_dict()
        try:
            return json.dumps(document, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise StructureNotJsonSerializable(str(exc)) from exc

    def ensure_json_compatible(self) -> None:
        self.to_jsonb_document()

    @classmethod
    def from_dict(cls, id_routine: int, data: dict) -> "RoutineStructure":
        if isinstance(data, list):
            blocks_data = data
        elif isinstance(data, dict):
            blocks_data = data.get("blocks", [])
        else:
            raise InvalidStructure(
                "The structure has to be an object whith 'blocks' or a list"
            )

        if not isinstance(blocks_data, list):
            raise InvalidStructure("'blocks' has to be a list.")

        return cls(
            id_routine=id_routine,
            blocks=[RoutineBlock.from_dict(block) for block in blocks_data],
        )
