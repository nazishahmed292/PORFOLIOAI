"""The migration itself: it applies, reverses, repeats, and never drifts from the models."""

import pytest
from alembic.script import ScriptDirectory
from alembic.util import CommandError
from sqlalchemy import inspect

import app.models  # noqa: F401  (registers the tables that APP_TABLES reads)
from app.database.base import Base

from .conftest import BACKEND_ROOT, run_alembic

APP_TABLES = set(Base.metadata.tables)


def table_names(engine) -> set[str]:
    return set(inspect(engine).get_table_names())


def test_history_has_a_single_head():
    from alembic.config import Config

    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    assert len(ScriptDirectory.from_config(config).get_heads()) == 1


def test_upgrade_creates_every_model_table(empty_engine):
    run_alembic(empty_engine, "upgrade", "head")
    assert table_names(empty_engine) == APP_TABLES | {"alembic_version"}


def test_downgrade_removes_everything_and_upgrade_can_repeat(empty_engine):
    run_alembic(empty_engine, "upgrade", "head")
    run_alembic(empty_engine, "downgrade", "base")
    assert table_names(empty_engine) == {"alembic_version"}

    run_alembic(empty_engine, "upgrade", "head")  # the round trip leaves nothing behind
    assert table_names(empty_engine) == APP_TABLES | {"alembic_version"}


def test_upgrade_is_idempotent(empty_engine):
    run_alembic(empty_engine, "upgrade", "head")
    run_alembic(empty_engine, "upgrade", "head")  # already at head: a no-op, not an error
    assert table_names(empty_engine) == APP_TABLES | {"alembic_version"}


def test_migrated_schema_matches_models_exactly(migrated_engine):
    """`alembic check` fails if the models changed without a migration (schema drift)."""
    run_alembic(migrated_engine, "check")


def test_check_detects_drift(migrated_engine):
    """Guards the guard: prove that the drift check above is actually able to fail."""
    from sqlalchemy import Column, Integer, Table

    Table("temporary_drift_probe", Base.metadata, Column("id", Integer, primary_key=True))
    try:
        with pytest.raises(CommandError):
            run_alembic(migrated_engine, "check")
    finally:
        Base.metadata.remove(Base.metadata.tables["temporary_drift_probe"])
