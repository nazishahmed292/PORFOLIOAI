"""Column types that behave the same on PostgreSQL (production) and SQLite (fast tests)."""

from typing import Any

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import JSON, Enum, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import MappedColumn, mapped_column

# Dimension of all-MiniLM-L6-v2, the default EMBEDDING_MODEL. It is baked into the
# schema (a pgvector column has a fixed size). Switching to a model with another
# dimension needs a migration that alters the column and re-embeds every chunk.
EMBEDDING_DIM = 384


class EmbeddingVector(VECTOR):
    """pgvector column that returns a plain ``list[float]``.

    Depending on the pgvector-python version the stock type returns a numpy array or a
    list, while the SQLite fallback returns a list. Normalising to a list of floats keeps
    service code identical on both databases and across library versions.
    Writing a vector of the wrong length raises ``ValueError`` before any SQL runs.
    """

    cache_ok = True

    def result_processor(self, dialect: Any, coltype: Any):
        parse = super().result_processor(dialect, coltype)

        def process(value: Any) -> list[float] | None:
            parsed = parse(value)
            return None if parsed is None else [float(x) for x in parsed]

        return process


def embedding_type(dim: int = EMBEDDING_DIM):
    """``vector(dim)`` on PostgreSQL, a JSON array on SQLite.

    ``none_as_null`` makes Python ``None`` a real SQL NULL rather than the JSON
    text ``null``, so "not embedded yet" is queryable with ``IS NULL``.
    """
    return EmbeddingVector(dim).with_variant(JSON(none_as_null=True), "sqlite")


def json_type():
    """JSONB on PostgreSQL (indexable, compact), plain JSON on SQLite."""
    return JSON(none_as_null=True).with_variant(JSONB(none_as_null=True), "postgresql")


def json_list(*args: Any, **kwargs: Any) -> MappedColumn:
    """NOT NULL JSON array column. Both Python and the database default to `[]`, so rows
    written by raw SQL, seed scripts or future migrations are valid too."""
    return mapped_column(*args, json_type(), default=list, server_default=text("'[]'"), **kwargs)


def json_object(*args: Any, **kwargs: Any) -> MappedColumn:
    """NOT NULL JSON object column, defaulting to `{}` in Python and in the database."""
    return mapped_column(*args, json_type(), default=dict, server_default=text("'{}'"), **kwargs)


def enum_type(enum_cls: type, name: str) -> Enum:
    """VARCHAR + CHECK constraint that stores the enum *value* (e.g. "in_progress")."""
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda members: [member.value for member in members],
    )
