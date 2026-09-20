"""Vector similarity search: only meaningful on PostgreSQL + pgvector."""

import random

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.models import EMBEDDING_DIM, DocumentChunk

from .factories import make_chunk, make_document, unit_vector

pytestmark = pytest.mark.postgres


@pytest.fixture(autouse=True)
def _only_on_postgres(backend):
    if backend != "postgresql":
        pytest.skip("pgvector operators exist only on PostgreSQL")


def as_literal(vector: list[float]) -> str:
    return "[" + ",".join(str(x) for x in vector) + "]"


def test_nearest_neighbour_by_cosine_distance(db):
    document = make_document(db)
    east = make_chunk(db, document, 0, content="east", embedding=unit_vector(0))
    north = make_chunk(db, document, 1, content="north", embedding=unit_vector(1))
    make_chunk(db, document, 2, content="up", embedding=unit_vector(2))
    close_to_east = [0.0] * EMBEDDING_DIM
    close_to_east[0], close_to_east[1] = 0.9, 0.1
    near = make_chunk(db, document, 3, content="near east", embedding=close_to_east)

    distance = DocumentChunk.embedding.cosine_distance(unit_vector(0))
    rows = db.execute(
        select(DocumentChunk.id, distance.label("distance"))
        .where(DocumentChunk.embedding.is_not(None))
        .order_by(distance)
        .limit(3)
    ).all()

    assert [r.id for r in rows[:2]] == [east.id, near.id]
    assert rows[0].distance == pytest.approx(0.0, abs=1e-6)  # identical direction
    assert rows[2].distance == pytest.approx(1.0, abs=1e-6)  # orthogonal
    assert north.id in {r.id for r in rows}


def test_chunks_without_an_embedding_can_be_excluded(db):
    document = make_document(db)
    make_chunk(db, document, 0)  # not embedded yet
    embedded = make_chunk(db, document, 1, embedding=unit_vector(3))

    ids = db.execute(
        select(DocumentChunk.id)
        .where(DocumentChunk.embedding.is_not(None))
        .order_by(DocumentChunk.embedding.cosine_distance(unit_vector(3)))
    ).scalars().all()
    assert ids == [embedded.id]


def test_similarity_search_can_be_filtered_by_document_visibility(db):
    from app.models import Document

    public, private = make_document(db), make_document(db, is_public=False)
    make_chunk(db, private, 0, embedding=unit_vector(0))
    visible = make_chunk(db, public, 0, embedding=unit_vector(0))

    ids = db.execute(
        select(DocumentChunk.id)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(Document.is_public.is_(True), DocumentChunk.embedding.is_not(None))
        .order_by(DocumentChunk.embedding.cosine_distance(unit_vector(0)))
    ).scalars().all()
    assert ids == [visible.id]


def test_postgres_itself_rejects_a_wrong_sized_vector(db):
    """Even code that bypasses the ORM cannot store a vector of the wrong length."""
    document = make_document(db)
    with pytest.raises(DBAPIError, match="dimensions"):
        db.execute(
            text(
                "INSERT INTO document_chunks (document_id, chunk_index, content, embedding) "
                "VALUES (:d, 0, 'x', CAST('[1,2,3]' AS vector))"
            ),
            {"d": document.id},
        )
    db.rollback()


def test_the_hnsw_index_is_used_for_nearest_neighbour_queries(db):
    rng = random.Random(7)
    document = make_document(db)
    for index in range(60):
        make_chunk(db, document, index, embedding=[rng.random() for _ in range(EMBEDDING_DIM)])
    db.flush()

    query = as_literal([rng.random() for _ in range(EMBEDDING_DIM)])
    db.execute(text("SET LOCAL enable_seqscan = off"))  # small table: force the planner's hand
    plan = "\n".join(
        row[0]
        for row in db.execute(
            text("EXPLAIN SELECT id FROM document_chunks ORDER BY embedding <=> CAST(:q AS vector) LIMIT 5"),
            {"q": query},
        )
    )
    assert "ix_document_chunks_embedding_hnsw" in plan


def test_jsonb_containment_query_on_chunk_metadata(db):
    document = make_document(db)
    match = make_chunk(db, document, 0, chunk_metadata={"section": "Skills", "tags": ["ml", "rag"]})
    make_chunk(db, document, 1, chunk_metadata={"section": "Education"})

    ids = db.execute(
        text("""SELECT id FROM document_chunks WHERE "metadata" @> CAST(:probe AS jsonb)"""),
        {"probe": '{"tags": ["rag"]}'},
    ).scalars().all()
    assert ids == [match.id]
