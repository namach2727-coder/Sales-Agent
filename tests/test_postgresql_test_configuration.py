from __future__ import annotations

import pytest

import conftest


def test_postgresql_database_url_alone_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(conftest.POSTGRES_TEST_URL_VARIABLE, raising=False)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:password@127.0.0.1/directpilot_test",
    )

    with pytest.raises(RuntimeError, match="DATABASE_URL alone is rejected"):
        conftest.configure_explicit_postgres_test_database()


@pytest.mark.parametrize(
    "url",
    [
        "sqlite:///./directpilot_test.db",
        "postgresql+psycopg://user:password@127.0.0.1/directpilot",
        "postgresql+psycopg://127.0.0.1/directpilot_test",
    ],
)
def test_postgresql_test_url_rejects_unsafe_targets(
    monkeypatch: pytest.MonkeyPatch,
    url: str,
) -> None:
    monkeypatch.setenv(conftest.POSTGRES_TEST_URL_VARIABLE, url)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError):
        conftest.configure_explicit_postgres_test_database()


def test_explicit_postgresql_test_url_configures_test_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    url = (
        "postgresql+psycopg://directpilot_test:directpilot_test@"
        "127.0.0.1:55432/directpilot_test"
    )
    monkeypatch.setenv(conftest.POSTGRES_TEST_URL_VARIABLE, url)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("APP_ENV", "development")

    assert conftest.configure_explicit_postgres_test_database() is True
    assert conftest.os.environ["DATABASE_URL"] == url
    assert conftest.os.environ["APP_ENV"] == "test"
