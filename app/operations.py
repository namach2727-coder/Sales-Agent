from __future__ import annotations

from dataclasses import dataclass

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.engine import Engine


@dataclass(frozen=True, slots=True)
class ReadinessResult:
    ready: bool
    database: str
    migration: str
    current_revision: str | None = None
    expected_revision: str | None = None


def expected_alembic_head() -> str:
    scripts = ScriptDirectory.from_config(Config("alembic.ini"))
    heads = scripts.get_heads()
    if len(heads) != 1:
        raise RuntimeError("migration graph must contain exactly one head")
    return heads[0]


def current_database_revision(engine: Engine) -> str | None:
    with engine.connect() as connection:
        try:
            return connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
        except Exception:
            return None


def readiness(engine: Engine) -> ReadinessResult:
    expected = expected_alembic_head()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return ReadinessResult(False, "unavailable", "unknown", expected_revision=expected)
    current = current_database_revision(engine)
    return ReadinessResult(
        ready=current == expected,
        database="available",
        migration="current" if current == expected else "out_of_date",
        current_revision=current,
        expected_revision=expected,
    )


def require_database_at_head(engine: Engine) -> None:
    result = readiness(engine)
    if not result.ready:
        raise RuntimeError(
            f"database is not ready (database={result.database}, migration={result.migration})"
        )
