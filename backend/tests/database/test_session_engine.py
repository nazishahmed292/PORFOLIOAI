"""The Phase 1 engine factory, extended so SQLite behaves like PostgreSQL for FK rules."""

from sqlalchemy import text

from app.database.session import build_engine


def test_sqlite_engine_enforces_foreign_keys(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'fk.db'}")
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1


def test_in_memory_sqlite_engine_enforces_foreign_keys():
    engine = build_engine("sqlite:///:memory:")
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
