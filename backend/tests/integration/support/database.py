"""Test-database lifecycle: create, migrate from the SQL scripts, and clean.

The tests never touch the development database: every destructive operation
checks that the target database name ends with ``_test``. The schema is applied
from ``backend/database/scripts/*.sql`` in file-name order, from Python, so the
``psql`` executable is not required.
"""

from __future__ import annotations

import pathlib

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from app.core.config import get_settings

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[3] / "database" / "scripts"
TEST_SUFFIX = "_test"
MAINTENANCE_DB = "postgres"


class UnsafeTestDatabase(RuntimeError):
    """Raised when a destructive operation targets a non-test database."""


def script_files() -> list[pathlib.Path]:
    """Schema scripts in the order they must be applied."""
    return sorted(SCRIPTS_DIR.glob("*.sql"))


def test_database_name() -> str:
    """Name of the dedicated test database."""
    return f"{get_settings().postgres_db}{TEST_SUFFIX}"


def ensure_test_database(name: str) -> None:
    """Refuse destructive work unless ``name`` is clearly a test database."""
    if not name.endswith(TEST_SUFFIX):
        raise UnsafeTestDatabase(
            f"Refusing to run destructive test operations on {name!r}: the name "
            f"must end with {TEST_SUFFIX!r}."
        )


def conninfo_for(database: str) -> str:
    settings = get_settings()
    values = conninfo_to_dict(
        make_conninfo(
            host=settings.postgres_host,
            port=settings.postgres_port,
            dbname=MAINTENANCE_DB,
            user=settings.postgres_user,
            password=settings.postgres_password.get_secret_value(),
        )
    )
    values["dbname"] = database
    return make_conninfo(**values)


def database_available() -> bool:
    """True when the maintenance database accepts the configured credentials."""
    try:
        with psycopg.connect(conninfo_for(MAINTENANCE_DB), connect_timeout=3):
            return True
    except (psycopg.Error, OSError):
        return False


def recreate_test_database(name: str | None = None) -> str:
    """Drop and create the test database; return its name."""
    target = name or test_database_name()
    ensure_test_database(target)

    with psycopg.connect(conninfo_for(MAINTENANCE_DB), autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                    sql.Identifier(target)
                )
            )
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target))
            )
    return target


def apply_scripts(name: str) -> list[str]:
    """Apply every schema script in order and return the applied file names."""
    ensure_test_database(name)

    applied: list[str] = []
    with psycopg.connect(conninfo_for(name), autocommit=True) as connection:
        for script in script_files():
            with connection.cursor() as cursor:
                cursor.execute(script.read_text(encoding="utf-8"))
            applied.append(script.name)
    return applied


async def truncate_all(connection: psycopg.AsyncConnection) -> None:
    """Empty every user table of the test database, resetting identities."""
    async with connection.cursor() as cursor:
        await cursor.execute("SELECT current_database() AS name")
        row = await cursor.fetchone()
        database = row["name"] if isinstance(row, dict) else row[0]
        ensure_test_database(database)

        await cursor.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )
        rows = await cursor.fetchall()
        tables = [
            (row["tablename"] if isinstance(row, dict) else row[0]) for row in rows
        ]
        if not tables:
            return
        await cursor.execute(
            sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(
                sql.SQL(", ").join(sql.Identifier(table) for table in tables)
            )
        )


