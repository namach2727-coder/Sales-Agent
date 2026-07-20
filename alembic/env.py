from __future__ import annotations

import logging

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import get_settings
from app.database import Base
from app import models  # noqa: F401 - registers every ORM model with Base.metadata


config = context.config


def configure_migration_logging() -> None:
    """Configure Alembic without resetting application-wide logging.

    ``logging.config.fileConfig`` clears and closes every registered handler in
    the current process before installing the handlers from ``alembic.ini``.
    That is surprising when migrations run in-process (for example from a test
    suite or an application startup hook), because unrelated application
    loggers can silently stop writing.  Alembic only needs its own logger here,
    so keep the configuration deliberately local and idempotent.
    """

    logger = logging.getLogger("alembic")
    handler = next(
        (
            candidate
            for candidate in logger.handlers
            if getattr(candidate, "_sales_agent_alembic_handler", False)
        ),
        None,
    )
    if handler is None:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)-5.5s [%(name)s] %(message)s"))
        handler._sales_agent_alembic_handler = True  # type: ignore[attr-defined]
        logger.addHandler(handler)

    logger.disabled = False
    logger.setLevel(logging.INFO)
    logger.propagate = False


configure_migration_logging()

target_metadata = Base.metadata


def database_url() -> str:
    override = config.attributes.get("database_url")
    return str(override or get_settings().database_url)


def run_migrations_offline() -> None:
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = database_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
