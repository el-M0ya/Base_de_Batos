"""JSONB serializers for ``RoutineStructure`` and routine persistence documents.

Converts between the domain ``RoutineStructure`` / ``RoutineBlock`` tree and
the JSONB document stored in ``routine_structure.structure_json``. The domain
layer never knows about psycopg or JSONB text; this module is the only place
that performs the conversion.
"""

from __future__ import annotations

import json
from typing import Optional

from app.domain.entities.routine_structure import RoutineStructure
from app.domain.exceptions.domain_exceptions import (
    InvalidStructure,
    StructureNotJsonSerializable,
)


def structure_to_jsonb(structure: RoutineStructure) -> str:
    """Serialize a ``RoutineStructure`` to the JSONB document string."""
    document = structure.to_dict()
    try:
        return json.dumps(document, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise StructureNotJsonSerializable(str(exc)) from exc


def jsonb_to_structure(id_routine: int, document: str) -> RoutineStructure:
    """Deserialize a JSONB document string into a ``RoutineStructure``.

    Accepts either a JSON string or a ``dict``/``list`` already parsed by the
    driver (dict_row returns parsed JSONB as Python objects).
    """
    if isinstance(document, (dict, list)):
        data = document
    elif isinstance(document, str):
        try:
            data = json.loads(document)
        except json.JSONDecodeError as exc:
            raise InvalidStructure(
                f"routine_structure document is not valid JSON: {exc}"
            ) from exc
    else:
        raise InvalidStructure(
            f"Unsupported structure document type: {type(document).__name__}"
        )

    return RoutineStructure.from_dict(id_routine, data)


def structure_document_from_rows(
    id_routine: int, blocks: Optional[list[dict]] = None
) -> str:
    """Build a minimal JSONB document from raw block dicts (test helper).

    Used only when assembling a structure document from persisted rows.
    """
    if blocks is None:
        blocks = []
    document = {"blocks": blocks}
    try:
        return json.dumps(document, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise StructureNotJsonSerializable(str(exc)) from exc
