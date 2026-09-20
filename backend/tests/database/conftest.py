"""Fixtures that build the schema with the real Alembic migration on a throwaway database.

Every test in this package runs twice: on SQLite (always) and on PostgreSQL with pgvector
(when a server is reachable). Because the schema comes from `alembic upgrade head` and not
from `create_all`, these tests prove that the *migration* produces a working schema.

PostgreSQL server: defaults to the one from `docker compose up -d db`. Point elsewhere with

    TEST_POSTGRES_URL=postgresql+psycopg://user:pass@host:5432/postgres

The user needs CREATE DATABASE rights. A fresh database is created per test session and
dropped afterwards, so your development data is never touched. Set REQUIRE_POSTGRES=1 (as
CI should) to make an unreachable server a failure instead of a skip.
"""

import os
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.session import build_engine

BACKEND_ROOT = Path(__file__).resolve().parents[2]
POSTGRES_ADMIN_URL = os.environ.get(
    "TEST_POSTGRES_URL", "postgresql+psycopg://portfolioai:portfolioai@localhost:5432/postgres"
)

BACKENDS = [
    pytest.param("sqlite", id="sqlite"),
    pytest.param("postgresql", id="postgresql", marks=pytest.mark.postgres),
]


# --- Alembic helpers ------------------------------------------------------------------


def run_alembic(engine: Engine, action: str, *args: str) -> None:
    """Run an Alembic command (upgrade, downgrade, check, ...) against `engine`."""
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection  # read by alembic/env.py
        getattr(command, action)(config, *args)


# --- Throwaway databases --------------------------------------------------------------


def postgres_unavailable_reason() -> str | None:
    try:
        engine = create_engine(POSTGRES_ADMIN_URL, connect_args={"connect_timeout": 3})
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        engine.dispose()
    except Exception as error:  # noqa: BLE001 - any failure means "not available"
        return f"PostgreSQL is not reachable at TEST_POSTGRES_URL ({type(error).__name__})"
    return None


@contextmanager
def temporary_database(backend: str, tmp_dir: Path) -> Iterator[Engine]:
    """Yield an engine for a brand-new, empty database; delete the database afterwards."""
    if backend == "sqlite":
        engine = build_engine(f"sqlite:///{tmp_dir / f'{uuid.uuid4().hex}.db'}")
        try:
            yield engine
        finally:
            engine.dispose()
        return

    reason = postgres_unavailable_reason()
    if reason:
        if os.environ.get("REQUIRE_POSTGRES"):
            pytest.fail(reason)
        pytest.skip(reason)

    name = f"portfolioai_test_{uuid.uuid4().hex[:12]}"
    admin = create_engine(POSTGRES_ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    url = make_url(POSTGRES_ADMIN_URL).set(database=name)
    engine = build_engine(url.render_as_string(hide_password=False))
    try:
        yield engine
    finally:
        engine.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        admin.dispose()


# --- Fixtures -------------------------------------------------------------------------


@pytest.fixture(scope="session", params=BACKENDS)
def migrated_engine(request, tmp_path_factory) -> Iterator[Engine]:
    """A database created by `alembic upgrade head`, shared by all tests of one backend."""
    with temporary_database(request.param, tmp_path_factory.mktemp("db")) as engine:
        run_alembic(engine, "upgrade", "head")
        yield engine


@pytest.fixture(params=BACKENDS)
def empty_engine(request, tmp_path) -> Iterator[Engine]:
    """A brand-new empty database per test (for migration up/down tests)."""
    with temporary_database(request.param, tmp_path) as engine:
        yield engine


@pytest.fixture()
def backend(migrated_engine: Engine) -> str:
    return migrated_engine.dialect.name


@pytest.fixture()
def db(migrated_engine: Engine) -> Iterator[Session]:
    """A session on the migrated database; every table is emptied after each test."""
    session = Session(migrated_engine, expire_on_commit=False, autoflush=False)
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        with migrated_engine.begin() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())


@pytest.fixture()
def insert_rejected(db: Session) -> Callable:
    r"""`insert_rejected(obj, by="ck_skills_proficiency_range")` asserts that the database
    refuses to store `obj` *because of that constraint*. `by` is a regex matched against
    the driver's error text, so a test cannot pass because of some unrelated failure.

    CHECK constraints are named identically on both databases (ck_<table>_<rule>). For
    unique and foreign-key violations PostgreSQL names the constraint while SQLite names
    the column, so those tests give both, e.g. by=r"ix_users_email|users\.email".
    """
    from sqlalchemy.exc import IntegrityError

    def check(*objects, by: str) -> None:
        # A SAVEPOINT undoes only the failed insert; the test's setup rows survive.
        with pytest.raises(IntegrityError, match=by):
            with db.begin_nested():
                db.add_all(objects)
                db.flush()

    return check
