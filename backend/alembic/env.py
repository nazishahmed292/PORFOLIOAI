"""Alembic environment: uses the app's settings and metadata."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.models  # noqa: F401  (registers every model on Base.metadata)
from app.core.config import get_settings
from app.database.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# '%' must be escaped for ConfigParser interpolation (e.g. URL-encoded passwords).
config.set_main_option("sqlalchemy.url", get_settings().database_url.replace("%", "%%"))
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def include_object(obj, name, type_, reflected, compare_to) -> bool:
    """Leave PostgreSQL-only indexes out of the comparison on other databases.

    The HNSW vector index is declared on the model but is only created on PostgreSQL
    (see the migration). Without this filter, `alembic check` on SQLite would report it
    as a missing index.
    """
    if type_ == "index" and name and name.endswith("_hnsw"):
        return context.get_context().dialect.name == "postgresql"
    return True


def _migrate(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        compare_type=True,
        render_as_batch=connection.dialect.name == "sqlite",
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Tests and tooling can hand in an open connection (config.attributes["connection"])
    # to migrate a specific database instead of the one named by DATABASE_URL.
    supplied = config.attributes.get("connection")
    if supplied is not None:
        _migrate(supplied)
        return

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        _migrate(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
