"""Static and executable validation for the project's Alembic history.

The command-line entry point intentionally creates disposable SQLite databases.
It never reads ``DATABASE_URL`` and never connects to the application's normal
database.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import re
import tempfile
from typing import Any, Iterable


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FILENAME_PATTERN = re.compile(
    r"^(?P<number>\d{4})_(?P<slug>[a-z][a-z0-9]*(?:_[a-z0-9]+)*)\.py$"
)
REVISION_PATTERN = re.compile(
    r"^(?P<number>\d{4})_(?P<slug>[a-z][a-z0-9]*(?:_[a-z0-9]+)*)$"
)
MAX_DESCRIPTION_LENGTH = 60
DESTRUCTIVE_ACK_NAME = "DESTRUCTIVE_MIGRATION_ACKNOWLEDGED"
EMPTY_DOWNGRADE_ACK_NAME = "EMPTY_DOWNGRADE_ALLOWED"


@dataclass(frozen=True)
class ValidationIssue:
    """One actionable migration-policy violation."""

    code: str
    message: str
    path: Path | None = None
    line: int | None = None

    def __str__(self) -> str:
        location = ""
        if self.path is not None:
            location = str(self.path)
            if self.line is not None:
                location += f":{self.line}"
            location += ": "
        return f"{location}[{self.code}] {self.message}"


@dataclass(frozen=True)
class RevisionSource:
    """Metadata and syntax extracted from one migration source file."""

    path: Path
    revision: str | None
    down_revision: str | tuple[str, ...] | None
    branch_labels: str | tuple[str, ...] | None
    depends_on: str | tuple[str, ...] | None
    destructive_acknowledged: bool
    empty_downgrade_allowed: bool
    tree: ast.Module


class MigrationValidationError(RuntimeError):
    """Raised when executable database validation finds a policy failure."""


def load_script_directory(repository_root: Path = REPOSITORY_ROOT):
    """Load Alembic's graph without opening a database connection."""

    from alembic.config import Config
    from alembic.script import ScriptDirectory

    root = repository_root.resolve()
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    return ScriptDirectory.from_config(config)


def _literal_assignment(tree: ast.Module, name: str) -> Any:
    for node in tree.body:
        value: ast.expr | None = None
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            value = node.value
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
        ):
            value = node.value
        if value is not None:
            try:
                return ast.literal_eval(value)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"{name} must be a Python literal") from exc
    raise KeyError(name)


def _optional_revision_value(value: Any, name: str) -> str | tuple[str, ...] | None:
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, (tuple, list)) and all(isinstance(item, str) for item in value):
        return tuple(value)
    raise ValueError(f"{name} must be None, a string, or a sequence of strings")


def parse_revision_source(path: Path) -> RevisionSource:
    """Parse revision metadata with AST; migration code is never imported."""

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def metadata(name: str) -> Any:
        try:
            return _literal_assignment(tree, name)
        except KeyError as exc:
            raise ValueError(f"required metadata {name!r} is missing") from exc

    return RevisionSource(
        path=path,
        revision=metadata("revision"),
        down_revision=_optional_revision_value(metadata("down_revision"), "down_revision"),
        branch_labels=_optional_revision_value(metadata("branch_labels"), "branch_labels"),
        depends_on=_optional_revision_value(metadata("depends_on"), "depends_on"),
        destructive_acknowledged=_literal_bool(tree, DESTRUCTIVE_ACK_NAME),
        empty_downgrade_allowed=_literal_bool(tree, EMPTY_DOWNGRADE_ACK_NAME),
        tree=tree,
    )


def _literal_bool(tree: ast.Module, name: str) -> bool:
    try:
        value = _literal_assignment(tree, name)
    except KeyError:
        return False
    return value is True


def _function(tree: ast.Module, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _function_is_empty(function: ast.FunctionDef | ast.AsyncFunctionDef | None) -> bool:
    if function is None:
        return True
    body = list(function.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        if isinstance(body[0].value.value, str):
            body.pop(0)
    return not body or all(
        isinstance(node, ast.Pass)
        or (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and node.value.value is Ellipsis
        )
        for node in body
    )


def _call_name(call: ast.Call) -> str | None:
    parts: list[str] = []
    value: ast.expr = call.func
    while isinstance(value, ast.Attribute):
        parts.append(value.attr)
        value = value.value
    if isinstance(value, ast.Name):
        parts.append(value.id)
    return ".".join(reversed(parts)) if parts else None


def _static_sql(expression: ast.expr) -> str | None:
    try:
        value = ast.literal_eval(expression)
    except (ValueError, TypeError):
        if isinstance(expression, ast.Call) and _call_name(expression) in {"sa.text", "text"}:
            return _static_sql(expression.args[0]) if expression.args else None
        return None
    return value if isinstance(value, str) else None


def detect_destructive_operations(source: RevisionSource) -> list[ValidationIssue]:
    """Find potentially destructive operations in the forward migration path."""

    upgrade = _function(source.tree, "upgrade")
    if upgrade is None:
        return []
    issues: list[ValidationIssue] = []
    destructive_calls = {
        "op.drop_table": "drops a table",
        "op.drop_column": "drops a column",
        "op.drop_constraint": "drops a constraint",
        "op.drop_index": "drops an index",
        "op.rename_table": "renames a table",
        "batch_op.drop_column": "drops a column",
        "batch_op.drop_constraint": "drops a constraint",
        "batch_op.drop_index": "drops an index",
        "batch_op.alter_column": "alters a column and may narrow compatibility",
        "op.alter_column": "alters a column and may narrow compatibility",
    }
    destructive_sql = re.compile(r"\b(DROP|TRUNCATE|DELETE|RENAME|REPLACE)\b", re.I)
    for node in ast.walk(upgrade):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        detail = destructive_calls.get(name or "")
        if name in {"op.execute", "batch_op.execute"}:
            sql = _static_sql(node.args[0]) if node.args else None
            if sql is None:
                detail = "executes dynamic SQL that cannot be proven non-destructive"
            elif destructive_sql.search(sql):
                detail = "executes potentially destructive SQL"
        if detail is not None:
            issues.append(
                ValidationIssue(
                    "destructive-operation",
                    f"{detail}; set {DESTRUCTIVE_ACK_NAME} = True only after explicit review",
                    source.path,
                    node.lineno,
                )
            )
    return issues


def detect_multitenant_violations(source: RevisionSource) -> list[ValidationIssue]:
    """Enforce safe introduction of tenant ownership on tables with existing rows."""

    upgrade = _function(source.tree, "upgrade")
    if upgrade is None:
        return []
    issues: list[ValidationIssue] = []
    for node in ast.walk(upgrade):
        if not isinstance(node, ast.Call) or _call_name(node) != "op.add_column":
            continue
        if len(node.args) < 2 or not isinstance(node.args[1], ast.Call):
            continue
        column_call = node.args[1]
        if _call_name(column_call) not in {"sa.Column", "Column"} or not column_call.args:
            continue
        try:
            column_name = ast.literal_eval(column_call.args[0])
        except (ValueError, TypeError):
            continue
        nullable_false = any(
            keyword.arg == "nullable"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is False
            for keyword in column_call.keywords
        )
        if column_name == "tenant_id" and nullable_false:
            issues.append(
                ValidationIssue(
                    "unsafe-tenant-column",
                    "add tenant_id as nullable, backfill deterministically, then enforce NOT NULL",
                    source.path,
                    node.lineno,
                )
            )
    return issues


def revision_files(versions_directory: Path) -> list[Path]:
    return sorted(
        path
        for path in versions_directory.glob("*.py")
        if path.name != "__init__.py"
    )


def validate_revision_files(versions_directory: Path) -> list[ValidationIssue]:
    """Validate names, metadata, implementations, and static safety policy."""

    issues: list[ValidationIssue] = []
    parsed: list[RevisionSource] = []
    files = revision_files(versions_directory)
    if not files:
        return [ValidationIssue("no-revisions", "no migration revisions were found", versions_directory)]

    seen_names: dict[str, Path] = {}
    for path in files:
        folded_name = path.name.casefold()
        if folded_name in seen_names:
            issues.append(
                ValidationIssue(
                    "duplicate-filename",
                    f"filename conflicts with {seen_names[folded_name].name}",
                    path,
                )
            )
        seen_names[folded_name] = path

        filename_match = FILENAME_PATTERN.fullmatch(path.name)
        if filename_match is None:
            issues.append(
                ValidationIssue(
                    "invalid-filename",
                    "use NNNN_short_snake_case_description.py with lowercase ASCII letters and digits",
                    path,
                )
            )
        elif len(filename_match.group("slug")) > MAX_DESCRIPTION_LENGTH:
            issues.append(
                ValidationIssue(
                    "description-too-long",
                    f"keep the filename description at or below {MAX_DESCRIPTION_LENGTH} characters",
                    path,
                )
            )

        try:
            source = parse_revision_source(path)
        except (SyntaxError, UnicodeError, ValueError) as exc:
            issues.append(ValidationIssue("invalid-revision", str(exc), path))
            continue
        parsed.append(source)

        if not isinstance(source.revision, str) or REVISION_PATTERN.fullmatch(source.revision) is None:
            issues.append(
                ValidationIssue(
                    "invalid-revision-id",
                    "revision must use NNNN_short_snake_case_description",
                    path,
                )
            )
        elif source.revision != path.stem:
            issues.append(
                ValidationIssue(
                    "revision-filename-mismatch",
                    f"revision {source.revision!r} must exactly match filename stem {path.stem!r}",
                    path,
                )
            )

        upgrade = _function(source.tree, "upgrade")
        downgrade = _function(source.tree, "downgrade")
        if _function_is_empty(upgrade):
            issues.append(
                ValidationIssue("empty-upgrade", "upgrade() must contain an operation", path)
            )
        if _function_is_empty(downgrade) and not source.empty_downgrade_allowed:
            issues.append(
                ValidationIssue(
                    "empty-downgrade",
                    f"downgrade() is empty; implement it or set {EMPTY_DOWNGRADE_ACK_NAME} = True with review",
                    path,
                )
            )
        destructive = detect_destructive_operations(source)
        if destructive and not source.destructive_acknowledged:
            issues.extend(destructive)
        issues.extend(detect_multitenant_violations(source))

    ids: dict[str, Path] = {}
    for source in parsed:
        if not isinstance(source.revision, str):
            continue
        if source.revision in ids:
            issues.append(
                ValidationIssue(
                    "duplicate-revision-id",
                    f"revision ID duplicates {ids[source.revision].name}",
                    source.path,
                )
            )
        ids[source.revision] = source.path
    return issues


def validate_migration_graph(repository_root: Path = REPOSITORY_ROOT) -> list[ValidationIssue]:
    """Validate that all known revisions form one reachable linear chain."""

    root = repository_root.resolve()
    versions = root / "alembic" / "versions"
    issues = validate_revision_files(versions)
    try:
        sources = [parse_revision_source(path) for path in revision_files(versions)]
    except (SyntaxError, UnicodeError, ValueError):
        return issues

    ids = {source.revision for source in sources if isinstance(source.revision, str)}
    children: dict[str, list[str]] = {revision: [] for revision in ids}
    roots: list[str] = []
    for source in sources:
        if not isinstance(source.revision, str):
            continue
        down = source.down_revision
        if isinstance(down, tuple):
            issues.append(
                ValidationIssue(
                    "merge-revision",
                    "merge revisions require an explicitly documented future policy exception",
                    source.path,
                )
            )
            continue
        if down is None:
            roots.append(source.revision)
        elif down not in ids:
            issues.append(
                ValidationIssue(
                    "missing-down-revision",
                    f"down_revision {down!r} does not exist",
                    source.path,
                )
            )
        else:
            children[down].append(source.revision)
        if source.branch_labels is not None:
            issues.append(
                ValidationIssue(
                    "branch-label",
                    "branch labels are not allowed while the migration history is linear",
                    source.path,
                )
            )
        if source.depends_on is not None:
            issues.append(
                ValidationIssue(
                    "cross-dependency",
                    "depends_on is not allowed in the current linear migration history",
                    source.path,
                )
            )

    if len(roots) != 1:
        issues.append(
            ValidationIssue("root-count", f"expected exactly one root revision, found {len(roots)}", versions)
        )
    for revision, revision_children in children.items():
        if len(revision_children) > 1:
            issues.append(
                ValidationIssue(
                    "migration-branch",
                    f"revision {revision!r} has multiple children: {', '.join(sorted(revision_children))}",
                    versions,
                )
            )
    heads = sorted(revision for revision, revision_children in children.items() if not revision_children)
    if len(heads) != 1:
        issues.append(
            ValidationIssue("head-count", f"expected exactly one migration head, found {len(heads)}", versions)
        )

    ordered = sorted(
        (source for source in sources if isinstance(source.revision, str)),
        key=lambda source: int(source.revision.split("_", 1)[0]),
    )
    for index, source in enumerate(ordered):
        expected_down = ordered[index - 1].revision if index else None
        if source.down_revision != expected_down:
            issues.append(
                ValidationIssue(
                    "nonlinear-chain",
                    f"expected down_revision {expected_down!r}, found {source.down_revision!r}",
                    source.path,
                )
            )
        if index:
            previous_number = int(ordered[index - 1].revision.split("_", 1)[0])
            current_number = int(source.revision.split("_", 1)[0])
            if current_number != previous_number + 1:
                issues.append(
                    ValidationIssue(
                        "revision-sequence-gap",
                        f"numeric prefix must follow {previous_number:04d} without gaps",
                        source.path,
                    )
                )

    if not issues:
        scripts = load_script_directory(root)
        alembic_heads = list(scripts.get_heads())
        if len(alembic_heads) != 1:
            issues.append(
                ValidationIssue(
                    "alembic-head-count",
                    f"Alembic reports {len(alembic_heads)} heads; expected exactly one",
                    versions,
                )
            )
        walked = list(scripts.walk_revisions())
        walked_ids = {revision.revision for revision in walked}
        if walked_ids != ids:
            missing = sorted(ids - walked_ids)
            extra = sorted(walked_ids - ids)
            issues.append(
                ValidationIssue(
                    "unreachable-revisions",
                    f"graph mismatch; unreachable={missing}, unexpected={extra}",
                    versions,
                )
            )
        if any(revision.is_merge_point for revision in walked):
            issues.append(
                ValidationIssue("merge-point", "Alembic graph contains a merge point", versions)
            )
    return issues


def _temporary_alembic_config(repository_root: Path, database_path: Path):
    from alembic.config import Config

    root = repository_root.resolve()
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    config.attributes["database_url"] = f"sqlite:///{database_path.as_posix()}"
    return config


def schema_drift_diagnostics(repository_root: Path, database_path: Path) -> list[str]:
    """Compare a migrated disposable database with registered ORM metadata."""

    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from sqlalchemy import create_engine

    from app import models  # noqa: F401 - registers all mapped tables
    from app.database import Base

    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(
                connection,
                opts={"compare_type": True, "compare_server_default": True},
            )
            return [repr(difference) for difference in compare_metadata(context, Base.metadata)]
    finally:
        engine.dispose()


def validate_schema_drift(repository_root: Path = REPOSITORY_ROOT) -> list[str]:
    """Upgrade an isolated database and return metadata drift diagnostics."""

    from alembic import command

    with tempfile.TemporaryDirectory(prefix="sales-agent-migration-drift-") as directory:
        database_path = Path(directory) / "schema.db"
        command.upgrade(_temporary_alembic_config(repository_root, database_path), "head")
        return schema_drift_diagnostics(repository_root, database_path)


def validate_round_trip(repository_root: Path = REPOSITORY_ROOT) -> list[str]:
    """Run base -> head -> base -> head against one disposable SQLite database."""

    from alembic import command
    from sqlalchemy import create_engine, inspect

    diagnostics: list[str] = []
    with tempfile.TemporaryDirectory(prefix="sales-agent-migration-roundtrip-") as directory:
        database_path = Path(directory) / "roundtrip.db"
        config = _temporary_alembic_config(repository_root, database_path)
        command.upgrade(config, "head")
        diagnostics.extend(schema_drift_diagnostics(repository_root, database_path))
        command.downgrade(config, "base")
        engine = create_engine(f"sqlite:///{database_path.as_posix()}")
        try:
            remaining = set(inspect(engine).get_table_names()) - {"alembic_version"}
        finally:
            engine.dispose()
        if remaining:
            diagnostics.append(f"tables remain after downgrade to base: {sorted(remaining)}")
        command.upgrade(config, "head")
        diagnostics.extend(schema_drift_diagnostics(repository_root, database_path))
    return diagnostics


def validate_all(repository_root: Path = REPOSITORY_ROOT) -> list[ValidationIssue]:
    """Run static, graph, schema-drift, and round-trip validation."""

    issues = validate_migration_graph(repository_root)
    if issues:
        return issues
    for diagnostic in validate_schema_drift(repository_root):
        issues.append(ValidationIssue("schema-drift", diagnostic))
    for diagnostic in validate_round_trip(repository_root):
        issues.append(ValidationIssue("round-trip", diagnostic))
    return issues


def _print_issues(issues: Iterable[ValidationIssue]) -> None:
    for issue in issues:
        print(f"ERROR {issue}")


def main() -> int:
    from alembic.util.exc import CommandError
    from sqlalchemy.exc import SQLAlchemyError

    print("Validating migration naming, metadata, safety, and graph...")
    try:
        issues = validate_all(REPOSITORY_ROOT)
    except (CommandError, MigrationValidationError, OSError, SQLAlchemyError, ValueError) as exc:
        print(f"ERROR migration validation could not complete: {exc}")
        return 2
    if issues:
        _print_issues(issues)
        print(f"Migration validation failed with {len(issues)} issue(s).")
        return 1
    scripts = load_script_directory(REPOSITORY_ROOT)
    print(f"Migration validation passed: one head ({scripts.get_current_head()}).")
    print("Schema drift and base -> head -> base -> head checks passed on temporary SQLite databases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
