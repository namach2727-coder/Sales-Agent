"""Fail-closed Neon UAT DSN validation; never log or return credentials."""
from __future__ import annotations

from urllib.parse import parse_qs, urlsplit


def validate_uat_database_url(url: str, expected_host: str) -> None:
    """Require the dedicated TelBot UAT role, database, host and TLS.

    Configured expected_host is the actual Neon UAT branch endpoint hostname.
    The function validates metadata only; it never connects or prints a DSN.
    """
    if not url or not expected_host or not expected_host.endswith(".neon.tech"):
        raise ValueError("TelBot UAT database config missing")
    try:
        parsed = urlsplit(url)
        settings = parse_qs(parsed.query, keep_blank_values=True)
        valid = (
            parsed.scheme in {"postgres", "postgresql"}
            and parsed.hostname == expected_host
            and parsed.username == "telbot_ua_runtime"
            and bool(parsed.password)
            and parsed.path == "/telbot"
            and parsed.port in {None, 5432}
            and parsed.fragment == ""
            and settings.get("sslmode") in (["require"], ["verify-full"])
        )
    except ValueError as exc:
        raise ValueError("Invalid TelBot UAT database config") from exc
    if not valid:
        raise ValueError("Invalid TelBot UAT database config")
