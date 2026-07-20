import ast
import importlib.util
import runpy
import sys
from types import ModuleType
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, inspect

from app.database import Base
from app import models  # noqa: F401 - registers metadata


ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_AVAILABLE = importlib.util.find_spec("alembic.config") is not None
requires_alembic = pytest.mark.skipif(
    not ALEMBIC_AVAILABLE,
    reason="Alembic is declared in requirements but unavailable in this environment",
)


def alembic_config(database_path: Path):
    from alembic.config import Config

    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite:///{database_path.as_posix()}"
    return config


def assignment_value(module: ast.Module, name: str):
    for node in module.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                return ast.literal_eval(node.value)
    raise AssertionError(f"{name} is not defined in baseline revision")


def test_baseline_source_tracks_all_application_tables() -> None:
    source = ROOT / "alembic" / "versions" / "0001_baseline_schema.py"
    module = ast.parse(source.read_text(encoding="utf-8"))
    table_order = assignment_value(module, "TABLE_ORDER")
    indexes = assignment_value(module, "INDEXES")
    assert set(table_order) == set(Base.metadata.tables)
    assert len(table_order) == 25
    expected_indexes = {
        index.name
        for table in Base.metadata.tables.values()
        for index in table.indexes
    }
    declared_indexes = {
        index_name
        for definitions in indexes.values()
        for index_name, _columns, _unique in definitions
    }
    assert declared_indexes == expected_indexes


def metadata_signature(metadata: sa.MetaData) -> dict:
    result = {}
    for table_name, table in metadata.tables.items():
        result[table_name] = {
            "columns": {
                column.name: (
                    str(column.type),
                    column.nullable,
                    column.primary_key,
                )
                for column in table.columns
            },
            "foreign_keys": {
                (
                    tuple(element.parent.name for element in constraint.elements),
                    tuple(element.target_fullname for element in constraint.elements),
                )
                for constraint in table.foreign_key_constraints
            },
            "unique": {
                (constraint.name, tuple(column.name for column in constraint.columns))
                for constraint in table.constraints
                if isinstance(constraint, sa.UniqueConstraint)
            },
            "indexes": {
                (
                    index.name,
                    tuple(column.name for column in index.columns),
                    index.unique,
                )
                for index in table.indexes
            },
        }
    return result


def test_baseline_operations_match_metadata_without_database(monkeypatch) -> None:
    class CaptureOperations:
        def __init__(self):
            self.metadata = sa.MetaData()

        def create_table(self, name, *elements):
            return sa.Table(name, self.metadata, *elements)

        def create_index(self, name, table_name, columns, unique=False):
            table = self.metadata.tables[table_name]
            sa.Index(name, *(table.c[column] for column in columns), unique=unique)

        def drop_index(self, name, *, table_name):
            table = self.metadata.tables[table_name]
            index = next(item for item in table.indexes if item.name == name)
            table.indexes.remove(index)

        def drop_table(self, name):
            self.metadata.remove(self.metadata.tables[name])

    operations = CaptureOperations()
    fake_alembic = ModuleType("alembic")
    fake_alembic.op = operations
    monkeypatch.setitem(sys.modules, "alembic", fake_alembic)
    namespace = runpy.run_path(
        str(ROOT / "alembic" / "versions" / "0001_baseline_schema.py")
    )
    namespace["upgrade"]()
    assert metadata_signature(operations.metadata) == metadata_signature(Base.metadata)
    namespace["downgrade"]()
    assert not operations.metadata.tables


@requires_alembic
def test_alembic_loads_with_one_baseline_head() -> None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config(str(ROOT / "alembic.ini"))
    scripts = ScriptDirectory.from_config(config)
    assert scripts.get_heads() == ["0001_baseline_schema"]
    revision = scripts.get_revision("0001_baseline_schema")
    assert revision is not None
    assert revision.down_revision is None


@requires_alembic
def test_baseline_upgrade_matches_registered_metadata(tmp_path) -> None:
    from alembic import command

    database_path = tmp_path / "upgrade.db"
    config = alembic_config(database_path)
    command.upgrade(config, "head")

    inspector = inspect(create_engine(f"sqlite:///{database_path.as_posix()}"))
    expected_tables = set(Base.metadata.tables)
    assert set(inspector.get_table_names()) == expected_tables | {"alembic_version"}
    for table_name, table in Base.metadata.tables.items():
        actual_columns = {
            column["name"]: (column["nullable"], bool(column.get("primary_key")))
            for column in inspector.get_columns(table_name)
        }
        expected_columns = {
            column.name: (column.nullable, column.primary_key)
            for column in table.columns
        }
        assert actual_columns == expected_columns
        assert {item["name"] for item in inspector.get_indexes(table_name)} == {
            index.name for index in table.indexes
        }
        actual_fks = {
            (
                tuple(item["constrained_columns"]),
                item["referred_table"],
                tuple(item["referred_columns"]),
            )
            for item in inspector.get_foreign_keys(table_name)
        }
        expected_fks = {
            (
                tuple(element.parent.name for element in constraint.elements),
                constraint.elements[0].column.table.name,
                tuple(element.column.name for element in constraint.elements),
            )
            for constraint in table.foreign_key_constraints
        }
        assert actual_fks == expected_fks


@requires_alembic
def test_migration_history_loads(tmp_path) -> None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config(str(ROOT / "alembic.ini"))
    scripts = ScriptDirectory.from_config(config)
    history = list(scripts.walk_revisions())
    assert [revision.revision for revision in history] == ["0001_baseline_schema"]


@requires_alembic
def test_upgrade_downgrade_upgrade_round_trip_uses_temporary_database(tmp_path) -> None:
    from alembic import command

    database_path = tmp_path / "round-trip.db"
    config = alembic_config(database_path)
    command.upgrade(config, "head")
    command.downgrade(config, "-1")
    after_downgrade = set(
        inspect(create_engine(f"sqlite:///{database_path.as_posix()}")).get_table_names()
    )
    assert after_downgrade <= {"alembic_version"}
    command.upgrade(config, "head")
    final_tables = set(
        inspect(create_engine(f"sqlite:///{database_path.as_posix()}")).get_table_names()
    )
    assert set(Base.metadata.tables).issubset(final_tables)
