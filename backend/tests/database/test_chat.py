"""Chat sessions, messages, and the citations attached to answers."""

import uuid

import pytest
from sqlalchemy import delete, text

from app.models import ChatMessage, ChatSession, DocumentChunk, MessageCitation, MessageRole

from .factories import make_chunk, make_document, make_session_with_message
from .helpers import count


def cite(db, message, marker=1, chunk=None, **overrides):
    citation = MessageCitation(
        message_id=message.id,
        chunk_id=chunk.id if chunk else None,
        marker=marker,
        source_title=overrides.pop("source_title", "Resume.pdf"),
        snippet=overrides.pop("snippet", "Built a GAT model."),
        **overrides,
    )
    db.add(citation)
    db.flush()
    return citation


def test_session_id_is_a_random_uuid(db):
    first, _ = make_session_with_message(db)
    second, _ = make_session_with_message(db)
    assert isinstance(first.id, uuid.UUID) and first.id != second.id
    db.expire_all()
    assert db.get(ChatSession, first.id).visitor_id == "visitor-1"


def test_messages_come_back_in_order(db):
    session, _ = make_session_with_message(db, MessageRole.USER)
    for text_ in ("second", "third"):
        db.add(ChatMessage(session_id=session.id, role=MessageRole.ASSISTANT, content=text_))
        db.flush()
    db.expire_all()
    assert [m.content for m in db.get(ChatSession, session.id).messages] == ["Hello", "second", "third"]


def test_deleting_a_session_deletes_messages_and_citations(db):
    session, message = make_session_with_message(db)
    cite(db, message, 1)
    cite(db, message, 2)

    db.execute(delete(ChatSession).where(ChatSession.id == session.id))
    assert count(db, ChatMessage) == 0
    assert count(db, MessageCitation) == 0


def test_a_message_needs_an_existing_session(db, insert_rejected):
    insert_rejected(
        ChatMessage(session_id=uuid.uuid4(), role=MessageRole.USER, content="lost"),
        by=r"fk_chat_messages_session_id_chat_sessions|FOREIGN KEY",
    )


def test_role_outside_the_enum_is_rejected(db):
    from sqlalchemy.exc import IntegrityError

    session, _ = make_session_with_message(db)
    sid = session.id.hex if db.bind.dialect.name == "sqlite" else str(session.id)  # CHAR(32) vs uuid
    with pytest.raises(IntegrityError, match="ck_chat_messages_message_role"):
        db.execute(
            text("INSERT INTO chat_messages (session_id, role, content) VALUES (:sid, 'robot', 'x')"),
            {"sid": sid},
        )
    db.rollback()


@pytest.mark.parametrize("value", [1, -1, None])
def test_feedback_accepts_thumbs_up_down_or_nothing(db, value):
    _, message = make_session_with_message(db)
    message.feedback = value
    db.flush()


@pytest.mark.parametrize("value", [0, 2, -2])
def test_feedback_rejects_other_values(db, insert_rejected, value):
    session, _ = make_session_with_message(db)
    insert_rejected(
        ChatMessage(session_id=session.id, role=MessageRole.USER, content="x", feedback=value),
        by="ck_chat_messages_feedback_values",
    )


def test_citation_marker_is_unique_per_message_and_positive(db, insert_rejected):
    _, message = make_session_with_message(db)
    cite(db, message, 1)
    insert_rejected(
        MessageCitation(message_id=message.id, marker=1, source_title="Dup", snippet="s"),
        by=r"uq_message_citations_message_id_marker|message_citations\.message_id",
    )
    insert_rejected(
        MessageCitation(message_id=message.id, marker=0, source_title="Zero", snippet="s"),
        by="ck_message_citations_marker_positive",
    )


def test_two_messages_may_reuse_the_same_marker(db):
    session, first = make_session_with_message(db)
    second = ChatMessage(session_id=session.id, role=MessageRole.ASSISTANT, content="again")
    db.add(second)
    db.flush()
    cite(db, first, 1)
    cite(db, second, 1)
    assert count(db, MessageCitation) == 2


def test_citations_are_ordered_by_marker(db):
    _, message = make_session_with_message(db)
    for marker in (3, 1, 2):
        cite(db, message, marker)
    db.expire_all()
    assert [c.marker for c in db.get(ChatMessage, message.id).citations] == [1, 2, 3]


def test_deleting_a_chunk_keeps_the_citation_snapshot(db):
    """Re-indexing replaces chunks; answers already given must still show their sources."""
    chunk = make_chunk(db, make_document(db), 0)
    _, message = make_session_with_message(db)
    citation = cite(db, message, 1, chunk=chunk, source_title="CancerBind report", page_number=4)

    db.execute(delete(DocumentChunk).where(DocumentChunk.id == chunk.id))
    db.refresh(citation)
    assert citation.chunk_id is None
    assert (citation.source_title, citation.page_number, citation.snippet) == (
        "CancerBind report",
        4,
        "Built a GAT model.",
    )


def test_deleting_a_document_cascades_to_chunks_and_detaches_citations(db):
    from app.models import Document

    document = make_document(db)
    chunk = make_chunk(db, document, 0)
    _, message = make_session_with_message(db)
    citation = cite(db, message, 1, chunk=chunk)

    db.execute(delete(Document).where(Document.id == document.id))
    db.refresh(citation)
    assert count(db, DocumentChunk) == 0 and citation.chunk_id is None
    assert count(db, MessageCitation) == 1
