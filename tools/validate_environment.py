from __future__ import annotations

import json

from app.config import get_settings, validate_runtime_settings


def main() -> int:
    try:
        settings = get_settings()
        validate_runtime_settings(settings)
    except Exception as exc:
        print(f"ERROR environment validation failed: {exc}")
        return 1
    print(
        json.dumps(
            {
                "status": "valid",
                "environment": settings.app_env,
                "database_dialect": settings.database_url.split(":", 1)[0],
                "json_logs": settings.json_logs,
                "secure_cookie": settings.session_cookie_secure,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
