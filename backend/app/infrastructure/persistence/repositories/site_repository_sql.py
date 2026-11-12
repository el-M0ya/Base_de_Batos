"""SQL implementation of ``SiteRepository`` over PostgreSQL with psycopg.

Persists gym sites with unique names (U-3). Deactivation is safe: it fails when
clients are associated with the site, so existing client records never end with
an invalid site reference.

All queries are explicit and parameterized.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from psycopg.errors import CheckViolation, ForeignKeyViolation, UniqueViolation

from app.application.exceptions import (
    BusinessRuleViolation,
    DuplicateResource,
    InvalidInput,
    ResourceNotFound,
)
from app.domain.entities.site import Site
from app.domain.repositories.site_repository import SiteRepository
from app.application.ports.transaction_manager import TransactionManager


def _row_to_site(row: dict) -> Site:
    """Map a database row (dict_row) to a ``Site`` domain entity."""
    return Site(
        id_site=row["id_site"],
        name=row["name"],
        address=row["address"],
        created_at=row["registration_date"],
    )


def _translate_error(error: Exception) -> Exception:
    """Translate a psycopg error into an application error."""
    detail = error.args[0] if error.args else ""
    if isinstance(error, UniqueViolation):
        return DuplicateResource("site", detail)
    if isinstance(error, ForeignKeyViolation):
        return BusinessRuleViolation(
            "the site cannot be removed because clients are associated with it; "
            "reassign or delete those clients first."
        )
    if isinstance(error, CheckViolation):
        return InvalidInput(detail)
    return error


class SiteRepositorySql(SiteRepository):
    """PostgreSQL adapter of ``SiteRepository``."""

    def __init__(self, transaction_manager: TransactionManager) -> None:
        self._tm = transaction_manager

    @property
    def _conn(self):
        conn = self._tm.connection()
        if conn is None:
            raise RuntimeError(
                "No transaction active. Use the repository inside a "
                "TransactionManager block."
            )
        return conn

    async def save(self, site: Site) -> Site:
        """Insert a new site and return it with its assigned identifier."""
        try:
            cursor = await self._conn.execute(
                """
                INSERT INTO site (name, address)
                VALUES (%s, %s)
                RETURNING id_site, name, address, registration_date
                """,
                (site.name, site.address),
            )
            row = await cursor.fetchone()
            if row is None:
                raise InvalidInput("the site insert did not return an identifier")
            saved = Site(
                id_site=row["id_site"],
                name=row["name"],
                address=row["address"],
                created_at=row["registration_date"],
            )
            return saved
        except UniqueViolation as error:
            raise _translate_error(error) from error

    async def get_by_id(self, id_site: int) -> Optional[Site]:
        """Return the site with that identifier, or ``None``."""
        try:
            cursor = await self._conn.execute(
                """
                SELECT id_site, name, address, registration_date
                FROM site
                WHERE id_site = %s
                """,
                (id_site,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return _row_to_site(row)
        except (ForeignKeyViolation, CheckViolation) as error:
            raise _translate_error(error) from error

    async def get_by_name(self, name: str) -> Optional[Site]:
        """Return the site with that name, or ``None``."""
        try:
            cursor = await self._conn.execute(
                """
                SELECT id_site, name, address, registration_date
                FROM site
                WHERE name = %s
                """,
                (name,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return _row_to_site(row)
        except (ForeignKeyViolation, CheckViolation) as error:
            raise _translate_error(error) from error

    async def list(self) -> list[Site]:
        """Return every site, ordered by name."""
        try:
            cursor = await self._conn.execute(
                """
                SELECT id_site, name, address, registration_date
                FROM site
                ORDER BY name ASC
                """
            )
            rows = await cursor.fetchall()
            return [_row_to_site(row) for row in rows]
        except (ForeignKeyViolation, CheckViolation) as error:
            raise _translate_error(error) from error

    async def update(self, site: Site) -> Site:
        """Update an existing site and return the stored entity."""
        try:
            cursor = await self._conn.execute(
                """
                UPDATE site
                SET name = %s,
                    address = %s
                WHERE id_site = %s
                RETURNING id_site, name, address, registration_date
                """,
                (site.name, site.address, site.id_site),
            )
            row = await cursor.fetchone()
            if row is None:
                raise ResourceNotFound("site", site.id_site)
            saved = Site(
                id_site=row["id_site"],
                name=row["name"],
                address=row["address"],
                created_at=row["registration_date"],
            )
            return saved
        except UniqueViolation as error:
            raise _translate_error(error) from error

    async def deactivate(self, id_site: int) -> None:
        """Deactivate a site by deleting it.

        Fails with ``BusinessRuleViolation`` when clients are associated with
        the site, preserving referential integrity.
        """
        try:
            cursor = await self._conn.execute(
                """
                DELETE FROM site
                WHERE id_site = %s
                RETURNING id_site
                """,
                (id_site,),
            )
            row = await cursor.fetchone()
            if row is None:
                raise ResourceNotFound("site", id_site)
        except ForeignKeyViolation as error:
            raise _translate_error(error) from error
