from __future__ import annotations

from pathlib import Path

import pytest

from app import config
from app.config import Settings


ROOT = Path(__file__).resolve().parents[1]


def _template_keys(path: Path) -> set[str]:
    return {
        line.partition("=")[0]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#") and "=" in line
    }


def test_no_profile_uses_canonical_env_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical = tmp_path / ".env"
    canonical.write_text("APP_NAME=Canonical settings\n", encoding="utf-8")
    monkeypatch.setattr(config, "ENV_FILE", canonical)
    monkeypatch.delenv(config.ENV_PROFILE_VARIABLE, raising=False)
    monkeypatch.delenv("APP_NAME", raising=False)

    assert config.resolve_startup_env_file() == canonical
    assert config.load_startup_settings().app_name == "Canonical settings"


def test_profile_is_selected_at_startup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dev = tmp_path / ".env.dev"
    uat = tmp_path / ".env.uat"
    dev.write_text(
        "APP_NAME=Development profile\nAPP_ENV=development\n",
        encoding="utf-8",
    )
    uat.write_text("APP_NAME=UAT profile\nAPP_ENV=uat\n", encoding="utf-8")
    monkeypatch.setattr(
        config,
        "ENV_PROFILE_FILES",
        {"dev": dev, "uat": uat, "production": tmp_path / ".env.production"},
    )
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setenv(config.ENV_PROFILE_VARIABLE, " UAT ")

    startup_settings = config.load_startup_settings()
    monkeypatch.setenv(config.ENV_PROFILE_VARIABLE, "dev")

    assert startup_settings.app_name == "UAT profile"
    assert startup_settings.app_env == "uat"


def test_application_settings_are_cached_after_startup() -> None:
    assert config.get_settings() is config.get_settings()


@pytest.mark.parametrize("profile", ["staging", "../production", ".env.dev"])
def test_unknown_or_path_like_profile_is_rejected(profile: str) -> None:
    with pytest.raises(ValueError, match="DIRECTPILOT_ENV_PROFILE"):
        config.resolve_startup_env_file(profile)


@pytest.mark.parametrize(
    ("file_name", "expected_environment"),
    [
        (".env.dev.example", "development"),
        (".env.uat.example", "uat"),
        (".env.production.example", "production"),
    ],
)
def test_profile_examples_are_valid_settings_templates(
    file_name: str,
    expected_environment: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)
    settings = Settings(_env_file=ROOT / file_name)

    assert settings.app_env == expected_environment


def test_profile_examples_derive_from_the_canonical_template() -> None:
    canonical_keys = _template_keys(ROOT / ".env.example")

    assert canonical_keys
    for file_name in (
        ".env.dev.example",
        ".env.uat.example",
        ".env.production.example",
    ):
        assert _template_keys(ROOT / file_name) == canonical_keys


@pytest.mark.parametrize("file_name", [".env.dev", ".env.uat", ".env.production"])
def test_local_profile_files_are_gitignored(file_name: str) -> None:
    ignore_rules = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert file_name in ignore_rules
    assert f"!{file_name}" not in ignore_rules
