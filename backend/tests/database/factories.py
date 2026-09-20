"""Small helpers that build valid rows so each test only spells out what it is about."""

from datetime import date
from itertools import count

from sqlalchemy.orm import Session

from app.models import (
    ChatMessage,
    ChatSession,
    Document,
    DocumentChunk,
    EMBEDDING_DIM,
    EvaluationQuestion,
    EvaluationRun,
    MessageRole,
    Project,
    RetrievalMode,
    Skill,
    User,
)

_ids = count(1)


def unit_vector(position: int, dim: int = EMBEDDING_DIM) -> list[float]:
    """A vector that is 1.0 at `position` and 0.0 elsewhere: easy to reason about."""
    vector = [0.0] * dim
    vector[position] = 1.0
    return vector


def make_user(db: Session, **overrides) -> User:
    n = next(_ids)
    values = {"email": f"user{n}@example.com", "hashed_password": "x" * 60, "full_name": f"User {n}"}
    user = User(**{**values, **overrides})
    db.add(user)
    db.flush()
    return user


def make_skill(db: Session, name: str = "Python", **overrides) -> Skill:
    skill = Skill(**{"name": name, "slug": name.lower(), **overrides})
    db.add(skill)
    db.flush()
    return skill


def make_project(db: Session, slug: str | None = None, **overrides) -> Project:
    n = next(_ids)
    slug = slug or f"project-{n}"
    project = Project(**{"slug": slug, "title": slug.title(), "summary": "A project.", **overrides})
    db.add(project)
    db.flush()
    return project


def make_document(db: Session, **overrides) -> Document:
    n = next(_ids)
    document = Document(**{"title": f"Document {n}", "sha256": f"{n:064x}", **overrides})
    db.add(document)
    db.flush()
    return document


def make_chunk(db: Session, document: Document, index: int = 0, **overrides) -> DocumentChunk:
    chunk = DocumentChunk(
        **{"document_id": document.id, "chunk_index": index, "content": f"chunk {index}", **overrides}
    )
    db.add(chunk)
    db.flush()
    return chunk


def make_session_with_message(db: Session, role: MessageRole = MessageRole.ASSISTANT):
    session = ChatSession(visitor_id="visitor-1")
    db.add(session)
    db.flush()
    message = ChatMessage(session_id=session.id, role=role, content="Hello")
    db.add(message)
    db.flush()
    return session, message


def make_run(db: Session, **overrides) -> EvaluationRun:
    run = EvaluationRun(**{"name": "baseline", "retrieval_mode": RetrievalMode.HYBRID, **overrides})
    db.add(run)
    db.flush()
    return run


def make_question(db: Session, **overrides) -> EvaluationQuestion:
    question = EvaluationQuestion(**{"question": "What is CancerBind?", **overrides})
    db.add(question)
    db.flush()
    return question


TODAY = date(2026, 9, 19)
