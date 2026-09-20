"""Inspect the migrated database itself (not the ORM) and compare it to the models."""

import pytest
from sqlalchemy import inspect, text

import app.models  # noqa: F401
from app.database.base import Base
from app.models import EMBEDDING_DIM


def test_every_column_of_every_model_exists(migrated_engine):
    inspector = inspect(migrated_engine)
    for table in Base.metadata.sorted_tables:
        actual = {column["name"] for column in inspector.get_columns(table.name)}
        expected = {column.name for column in table.columns}
        assert actual == expected, f"column mismatch in {table.name}"


def test_foreign_keys_match_the_models(migrated_engine):
    inspector = inspect(migrated_engine)
    for table in Base.metadata.sorted_tables:
        actual = {
            (tuple(fk["constrained_columns"]), fk["referred_table"], (fk["options"].get("ondelete") or "").upper())
            for fk in inspector.get_foreign_keys(table.name)
        }
        expected = {
            (
                tuple(column.name for column in fk.columns),
                fk.referred_table.name,
                (fk.ondelete or "").upper(),
            )
            for fk in table.foreign_key_constraints
        }
        assert actual == expected, f"foreign key mismatch in {table.name}"


def test_every_constraint_has_an_explicit_name():
    """Named constraints make later migrations (drop/alter) deterministic on every database."""
    for table in Base.metadata.sorted_tables:
        for constraint in table.constraints:
            assert constraint.name, f"unnamed {type(constraint).__name__} on {table.name}"


def test_unique_and_primary_keys_exist(migrated_engine):
    inspector = inspect(migrated_engine)
    assert inspector.get_pk_constraint("users")["constrained_columns"] == ["id"]
    assert inspector.get_pk_constraint("project_skills")["constrained_columns"] == [
        "project_id",
        "skill_id",
    ]
    unique_sets = {
        tuple(uc["column_names"]) for uc in inspector.get_unique_constraints("document_chunks")
    }
    assert ("document_id", "chunk_index") in unique_sets


def test_backend_specific_column_types(migrated_engine, backend):
    columns = {c["name"]: c for c in inspect(migrated_engine).get_columns("document_chunks")}
    sessions_id = {c["name"]: c for c in inspect(migrated_engine).get_columns("chat_sessions")}["id"]
    if backend == "postgresql":
        with migrated_engine.connect() as connection:
            row = connection.execute(
                text(
                    "SELECT format_type(atttypid, atttypmod) FROM pg_attribute "
                    "WHERE attrelid = 'document_chunks'::regclass AND attname = 'embedding'"
                )
            ).scalar_one()
        assert row == f"vector({EMBEDDING_DIM})"
        assert columns["metadata"]["type"].__class__.__name__ == "JSONB"
        assert sessions_id["type"].__class__.__name__ == "UUID"
    else:
        assert columns["embedding"]["type"].__class__.__name__ == "JSON"
        assert columns["metadata"]["type"].__class__.__name__ == "JSON"


@pytest.mark.postgres
def test_postgres_has_hnsw_cosine_index(migrated_engine, backend):
    if backend != "postgresql":
        pytest.skip("PostgreSQL only")
    with migrated_engine.connect() as connection:
        definition = connection.execute(
            text("SELECT indexdef FROM pg_indexes WHERE indexname = 'ix_document_chunks_embedding_hnsw'")
        ).scalar_one()
        extension = connection.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        ).scalar_one()
    assert "USING hnsw" in definition and "vector_cosine_ops" in definition
    assert extension == "vector"


def test_sqlite_skips_the_vector_index(migrated_engine, backend):
    if backend != "sqlite":
        pytest.skip("SQLite only")
    index_names = {index["name"] for index in inspect(migrated_engine).get_indexes("document_chunks")}
    assert "ix_document_chunks_embedding_hnsw" not in index_names


def test_every_required_json_column_has_a_database_default(migrated_engine):
    """Raw SQL, seed scripts and data migrations must be able to omit JSON columns.

    Guards every NOT NULL JSON column, including ones added in later phases. (`alembic check`
    does not compare server defaults, so nothing else would notice a missing one.)
    """
    from sqlalchemy import JSON

    inspector = inspect(migrated_engine)
    checked = 0
    for table in Base.metadata.sorted_tables:
        actual = {c["name"]: c for c in inspector.get_columns(table.name)}
        for column in table.columns:
            if isinstance(column.type, JSON) and not column.nullable:
                assert actual[column.name]["default"] is not None, f"{table.name}.{column.name}"
                checked += 1
    assert checked == 15  # update when a JSON column is added; the loop above is the real guard
