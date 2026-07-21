from __future__ import annotations

from alembic import command
from alembic.config import Config

from app.config import get_settings, validate_runtime_settings
from app.database import build_engine
from app.operations import require_database_at_head


def main() -> int:
    settings = get_settings()
    engine = None
    try:
        validate_runtime_settings(settings)
        print("Validating one-head migration graph...")
        config = Config("alembic.ini")
        print("Applying Alembic migrations to head...")
        command.upgrade(config, "head")
        engine = build_engine(settings)
        require_database_at_head(engine)
        print("Database migration completed and current head was verified.")
        return 0
    except Exception:
        print("ERROR migration failed; deployment must not continue")
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
