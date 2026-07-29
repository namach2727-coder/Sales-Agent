from __future__ import annotations

from pathlib import Path

from alembic import command
from sqlalchemy import create_engine, text

from tools.migration_policy import (
    detect_destructive_operations,
    load_script_directory,
    parse_revision_source,
    schema_drift_diagnostics,
    validate_migration_graph,
    validate_revision_files,
    validate_round_trip,
    validate_schema_drift,
)


ROOT = Path(__file__).resolve().parents[1]


def _write_revision(
    versions: Path,
    filename: str,
    *,
    revision: str | None = None,
    down_revision: str | None = None,
    upgrade: str = "op.create_table('example')",
    downgrade: str = "op.drop_table('example')",
    destructive_acknowledged: bool = False,
    empty_downgrade_allowed: bool = False,
) -> Path:
    versions.mkdir(parents=True, exist_ok=True)
    revision = revision or Path(filename).stem
    path = versions / filename
    path.write_text(
        "\n".join(
            [
                "from alembic import op",
                f"revision = {revision!r}",
                f"down_revision = {down_revision!r}",
                "branch_labels = None",
                "depends_on = None",
                f"DESTRUCTIVE_MIGRATION_ACKNOWLEDGED = {destructive_acknowledged!r}",
                f"EMPTY_DOWNGRADE_ALLOWED = {empty_downgrade_allowed!r}",
                "",
                "def upgrade():",
                f"    {upgrade}",
                "",
                "def downgrade():",
                f"    {downgrade}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _issue_codes(versions: Path) -> set[str]:
    return {issue.code for issue in validate_revision_files(versions)}


def _temporary_config(database_path: Path):
    from alembic.config import Config

    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.attributes["database_url"] = f"sqlite:///{database_path.as_posix()}"
    return config


def test_current_migration_history_satisfies_policy() -> None:
    assert validate_migration_graph(ROOT) == []


def test_current_history_has_exactly_one_head_and_valid_baseline_name() -> None:
    scripts = load_script_directory(ROOT)
    assert scripts.get_heads() == ["0009_conversation_core_models"]
    baseline = ROOT / "alembic" / "versions" / "0001_baseline_schema.py"
    assert parse_revision_source(baseline).revision == baseline.stem


def test_invalid_revision_filename_is_rejected(tmp_path: Path) -> None:
    versions = tmp_path / "versions"
    _write_revision(versions, "Bad-Migration.py", revision="0001_valid_name")
    assert "invalid-filename" in _issue_codes(versions)


def test_duplicate_revision_ids_are_rejected(tmp_path: Path) -> None:
    versions = tmp_path / "versions"
    _write_revision(versions, "0001_first.py")
    _write_revision(versions, "0002_second.py", revision="0001_first")
    assert "duplicate-revision-id" in _issue_codes(versions)


def test_empty_upgrade_is_rejected(tmp_path: Path) -> None:
    versions = tmp_path / "versions"
    _write_revision(versions, "0001_empty_upgrade.py", upgrade="pass")
    assert "empty-upgrade" in _issue_codes(versions)


def test_empty_downgrade_requires_explicit_allowance(tmp_path: Path) -> None:
    versions = tmp_path / "versions"
    _write_revision(versions, "0001_empty_downgrade.py", downgrade="pass")
    assert "empty-downgrade" in _issue_codes(versions)

    allowed = tmp_path / "allowed"
    _write_revision(
        allowed,
        "0001_irreversible_change.py",
        downgrade="pass",
        empty_downgrade_allowed=True,
    )
    assert "empty-downgrade" not in _issue_codes(allowed)


def test_destructive_operation_requires_acknowledgement(tmp_path: Path) -> None:
    versions = tmp_path / "versions"
    _write_revision(versions, "0001_drop_legacy_table.py", upgrade="op.drop_table('legacy')")
    assert "destructive-operation" in _issue_codes(versions)


def test_acknowledged_destructive_operation_remains_detectable_but_is_allowed(
    tmp_path: Path,
) -> None:
    versions = tmp_path / "versions"
    path = _write_revision(
        versions,
        "0001_drop_legacy_table.py",
        upgrade="op.drop_table('legacy')",
        destructive_acknowledged=True,
    )
    source = parse_revision_source(path)
    assert source.destructive_acknowledged is True
    assert detect_destructive_operations(source)
    assert "destructive-operation" not in _issue_codes(versions)


def test_immediately_non_nullable_tenant_id_is_rejected(tmp_path: Path) -> None:
    versions = tmp_path / "versions"
    _write_revision(
        versions,
        "0001_add_tenant_id.py",
        upgrade="op.add_column('orders', sa.Column('tenant_id', sa.Integer(), nullable=False))",
    )
    assert "unsafe-tenant-column" in _issue_codes(versions)


def test_schema_drift_detection_reports_unmanaged_table(tmp_path: Path) -> None:
    database_path = tmp_path / "drift.db"
    command.upgrade(_temporary_config(database_path), "head")
    assert schema_drift_diagnostics(ROOT, database_path) == []

    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE unmanaged_table (id INTEGER PRIMARY KEY)"))
    finally:
        engine.dispose()
    diagnostics = schema_drift_diagnostics(ROOT, database_path)
    assert any("unmanaged_table" in diagnostic for diagnostic in diagnostics)


def test_upgrade_downgrade_upgrade_round_trip_succeeds() -> None:
    assert validate_round_trip(ROOT) == []


def test_validation_never_modifies_configured_application_database(
    tmp_path: Path, monkeypatch
) -> None:
    protected_path = tmp_path / "application.db"
    engine = create_engine(f"sqlite:///{protected_path.as_posix()}")
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE protected_marker (id INTEGER PRIMARY KEY)"))
    finally:
        engine.dispose()
    before = protected_path.read_bytes()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{protected_path.as_posix()}")

    assert validate_schema_drift(ROOT) == []
    assert validate_round_trip(ROOT) == []
    assert protected_path.read_bytes() == before
