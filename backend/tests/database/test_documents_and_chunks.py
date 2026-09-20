"""Documents, chunks and embeddings."""

import numpy as np
import pytest
from sqlalchemy import delete, select, text

from app.models import (
    EMBEDDING_DIM,
    Document,
    DocumentChunk,
    DocumentKind,
    DocumentStatus,
    User,
)
from app.models import Project

from .factories import make_chunk, make_document, make_project, make_user, unit_vector
from .helpers import count


# ---- documents -----------------------------------------------------------------------


def test_document_defaults(db):
    document = make_document(db)
    db.refresh(document)
    assert document.kind is DocumentKind.OTHER
    assert document.status is DocumentStatus.UPLOADED
    assert document.chunk_count == 0
    assert document.is_public is True


def test_the_same_file_cannot_be_registered_twice(db, insert_rejected):
    make_document(db, sha256="a" * 64)
    insert_rejected(
        Document(title="Duplicate", sha256="a" * 64), by=r"uq_documents_sha256|documents\.sha256"
    )


def test_documents_without_a_hash_do_not_collide(db):
    """Generated documents have no file, so no hash: NULLs must not violate uniqueness."""
    make_document(db, sha256=None, kind=DocumentKind.PORTFOLIO_GENERATED)
    make_document(db, sha256=None, kind=DocumentKind.PORTFOLIO_GENERATED)
    assert count(db, Document) == 2


def test_hash_must_be_64_characters(db, insert_rejected):
    insert_rejected(Document(title="Bad hash", sha256="abc"), by="ck_documents_sha256_length")


def test_negative_file_size_is_rejected(db, insert_rejected):
    insert_rejected(Document(title="Negative", file_size_bytes=-1), by="ck_documents_size_positive")


def test_deleting_the_uploader_keeps_the_document(db):
    user = make_user(db)
    document = make_document(db, owner_id=user.id)

    db.execute(delete(User).where(User.id == user.id))
    db.refresh(document)
    assert document.owner_id is None
    assert count(db, Document) == 1


def test_deleting_a_project_keeps_its_document(db):
    project = make_project(db)
    document = make_document(db, project_id=project.id)

    db.execute(delete(Project).where(Project.id == project.id))
    db.refresh(document)
    assert document.project_id is None


def test_deleting_a_document_deletes_its_chunks(db):
    document = make_document(db)
    make_chunk(db, document, 0)
    make_chunk(db, document, 1)
    other = make_document(db)
    make_chunk(db, other, 0)

    db.execute(delete(Document).where(Document.id == document.id))
    assert count(db, DocumentChunk) == 1  # only the other document's chunk survives


def test_chunks_come_back_in_document_order(db):
    document = make_document(db)
    for index in (2, 0, 1):
        make_chunk(db, document, index)
    db.expire_all()
    assert [c.chunk_index for c in db.get(Document, document.id).chunks] == [0, 1, 2]


# ---- chunks --------------------------------------------------------------------------


def test_chunk_position_is_unique_within_a_document(db, insert_rejected):
    document = make_document(db)
    make_chunk(db, document, 0)
    insert_rejected(
        DocumentChunk(document_id=document.id, chunk_index=0, content="again"),
        by=r"uq_document_chunks_document_id_chunk_index|document_chunks\.document_id",
    )


def test_the_same_position_may_exist_in_different_documents(db):
    make_chunk(db, make_document(db), 0)
    make_chunk(db, make_document(db), 0)
    assert count(db, DocumentChunk) == 2


def test_chunk_index_cannot_be_negative(db, insert_rejected):
    document = make_document(db)
    insert_rejected(
        DocumentChunk(document_id=document.id, chunk_index=-1, content="x"),
        by="ck_document_chunks_index_positive",
    )


def test_chunk_needs_an_existing_document(db, insert_rejected):
    insert_rejected(
        DocumentChunk(document_id=999_999, chunk_index=0, content="orphan"),
        by=r"fk_document_chunks_document_id_documents|FOREIGN KEY",
    )


def test_chunk_metadata_roundtrip_and_default(db):
    document = make_document(db)
    rich = make_chunk(
        db, document, 0, chunk_metadata={"section": "Intro", "tags": ["gat", "drug"], "n": 3}
    )
    plain = make_chunk(db, document, 1)
    db.expire_all()
    assert db.get(DocumentChunk, rich.id).chunk_metadata == {"section": "Intro", "tags": ["gat", "drug"], "n": 3}
    assert db.get(DocumentChunk, plain.id).chunk_metadata == {}


# ---- embeddings ----------------------------------------------------------------------


def test_embedding_roundtrip_returns_a_plain_list(db):
    vector = [round(0.001 * i, 6) for i in range(EMBEDDING_DIM)]
    chunk = make_chunk(db, make_document(db), 0, embedding=vector, embedding_model="all-MiniLM-L6-v2")
    db.expire_all()

    loaded = db.get(DocumentChunk, chunk.id).embedding
    assert isinstance(loaded, list) and not isinstance(loaded, np.ndarray)
    assert loaded == pytest.approx(vector, abs=1e-6)  # pgvector stores float32


def test_embedding_defaults_to_a_real_sql_null(db):
    """'Not embedded yet' must be queryable with IS NULL (not the JSON text 'null')."""
    document = make_document(db)
    pending = make_chunk(db, document, 0)
    make_chunk(db, document, 1, embedding=unit_vector(0))
    db.expire_all()

    assert db.get(DocumentChunk, pending.id).embedding is None
    waiting = db.execute(select(DocumentChunk.id).where(DocumentChunk.embedding.is_(None))).scalars().all()
    assert waiting == [pending.id]
    assert db.execute(text("SELECT count(*) FROM document_chunks WHERE embedding IS NULL")).scalar_one() == 1


@pytest.mark.parametrize("size", [0, 3, EMBEDDING_DIM - 1, EMBEDDING_DIM + 1])
def test_wrong_embedding_dimension_is_refused_before_any_sql(db, size):
    document = make_document(db)
    with pytest.raises(ValueError, match=str(EMBEDDING_DIM)):
        DocumentChunk(document_id=document.id, chunk_index=0, content="x", embedding=[0.1] * size)


def test_embedding_can_be_cleared_again(db):
    chunk = make_chunk(db, make_document(db), 0, embedding=unit_vector(5))
    chunk.embedding = None
    db.flush()
    db.expire_all()
    assert db.get(DocumentChunk, chunk.id).embedding is None
