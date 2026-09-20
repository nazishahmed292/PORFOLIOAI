"""Uploaded documents and the text chunks (with embeddings) that RAG retrieves from."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.database.base import Base, TimestampMixin
from app.models.enums import DocumentKind, DocumentStatus
from app.models.column_types import EMBEDDING_DIM, embedding_type, enum_type, json_object

if TYPE_CHECKING:
    from app.models.chat import MessageCitation
    from app.models.portfolio import Project
    from app.models.user import User


class Document(TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("sha256 IS NULL OR length(sha256) = 64", name="sha256_length"),
        CheckConstraint("file_size_bytes IS NULL OR file_size_bytes >= 0", name="size_positive"),
        CheckConstraint("chunk_count >= 0", name="chunk_count_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Keep the document (and its chunks) if the uploading account is deleted.
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    # Optional link: "this PDF is the write-up of project X".
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str | None] = mapped_column(String(255))
    stored_path: Mapped[str | None] = mapped_column(String(500))  # NULL for generated documents
    content_type: Mapped[str | None] = mapped_column(String(100))
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    # SHA-256 of the file bytes: re-uploading the same file is detected and rejected.
    sha256: Mapped[str | None] = mapped_column(String(64), unique=True)
    kind: Mapped[DocumentKind] = mapped_column(
        enum_type(DocumentKind, "document_kind"),
        default=DocumentKind.OTHER,
        server_default=DocumentKind.OTHER.value,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        enum_type(DocumentStatus, "document_status"),
        default=DocumentStatus.UPLOADED,
        server_default=DocumentStatus.UPLOADED.value,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    page_count: Mapped[int | None] = mapped_column(Integer)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    # Private documents are indexed for the owner's tools but never cited to visitors.
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    owner: Mapped["User | None"] = relationship()
    project: Mapped["Project | None"] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="DocumentChunk.chunk_index",
    )


class DocumentChunk(TimestampMixin, Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        # Also serves lookups by document_id, since it is the leading column.
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_document_id_chunk_index"),
        CheckConstraint("chunk_index >= 0", name="index_positive"),
        # Approximate nearest-neighbour index for cosine search (PostgreSQL only).
        # HNSW needs no training data, so it works on an empty or growing table.
        Index(
            "ix_document_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ).ddl_if(dialect="postgresql"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_index: Mapped[int] = mapped_column(Integer)  # position within the document
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int | None] = mapped_column(Integer)
    page_number: Mapped[int | None] = mapped_column(Integer)
    section_title: Mapped[str | None] = mapped_column(String(255))
    # Column is called "metadata" in SQL; the attribute cannot use that name because
    # SQLAlchemy reserves `metadata` on declarative classes.
    chunk_metadata: Mapped[dict[str, Any]] = json_object("metadata")
    # NULL until the embedding step has run for this chunk.
    embedding: Mapped[list[float] | None] = mapped_column(embedding_type())
    embedding_model: Mapped[str | None] = mapped_column(String(200))

    document: Mapped[Document] = relationship(back_populates="chunks")
    citations: Mapped[list["MessageCitation"]] = relationship(back_populates="chunk")

    @validates("embedding")
    def _check_embedding_dimension(self, _key: str, value: list[float] | None):
        # Fail fast and identically on SQLite and PostgreSQL.
        if value is not None and len(value) != EMBEDDING_DIM:
            raise ValueError(f"embedding must have {EMBEDDING_DIM} values, got {len(value)}")
        return value
