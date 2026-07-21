from __future__ import annotations

from app.config import get_settings, validate_runtime_settings
from app.database import build_engine, check_database_connection


def main() -> int:
    settings = get_settings()
    engine = None
    try:
        validate_runtime_settings(settings)
        engine = build_engine(settings)
        check_database_connection(engine)
        print("Database connectivity check passed.")
        return 0
    except Exception:
        print("ERROR database connectivity check failed; connection details were redacted")
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
