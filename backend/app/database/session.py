"""Engine and session factory, plus the FastAPI dependency that hands a session
to each request and always closes it afterwards."""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings


def build_engine(database_url: str, *, echo: bool = False) -> Engine:
    if database_url.startswith("sqlite"):
        # SQLite is only used for fast unit tests. An in-memory database needs a
        # single shared connection, otherwise every connection sees an empty DB.
        kwargs: dict = {"connect_args": {"check_same_thread": False}}
        if ":memory:" in database_url or database_url.rstrip("/") == "sqlite:":
            kwargs["poolclass"] = StaticPool
        sqlite_engine = create_engine(database_url, echo=echo, **kwargs)

        # SQLite ignores FOREIGN KEY rules unless asked, on every new connection. Without
        # this, tests on SQLite would accept rows that PostgreSQL rejects (and would skip
        # ON DELETE CASCADE / SET NULL), so the two databases would behave differently.
        @event.listens_for(sqlite_engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return sqlite_engine

    return create_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,  # transparently replace dead connections
        pool_size=5,
        max_overflow=10,
    )


_settings = get_settings()
engine = build_engine(_settings.database_url, echo=_settings.debug)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: one session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
