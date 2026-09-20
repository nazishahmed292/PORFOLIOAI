"""RAG evaluation: a question set, runs of that set, and per-question results (Phase 10)."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.enums import FailureType, QuestionCategory, RetrievalMode, RunStatus
from app.models.column_types import enum_type, json_list, json_object

_UNIT_METRICS = ("reciprocal_rank", "precision_at_k", "recall_at_k", "faithfulness", "answer_relevance")


def _unit_interval(column: str) -> CheckConstraint:
    """A metric is either not computed yet (NULL) or a number between 0 and 1."""
    return CheckConstraint(
        f"{column} IS NULL OR ({column} >= 0 AND {column} <= 1)", name=f"{column}_range"
    )


class EvaluationQuestion(TimestampMixin, Base):
    __tablename__ = "evaluation_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset: Mapped[str] = mapped_column(String(100), default="default", server_default="default", index=True)
    question: Mapped[str] = mapped_column(Text)
    ground_truth: Mapped[str | None] = mapped_column(Text)  # reference answer; NULL if unanswerable
    category: Mapped[QuestionCategory] = mapped_column(
        enum_type(QuestionCategory, "question_category"),
        default=QuestionCategory.FACTUAL,
        server_default=QuestionCategory.FACTUAL.value,
    )
    # False for questions the corpus cannot answer: the right behaviour is to decline.
    is_answerable: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    # Titles of the documents that contain the answer (titles survive re-uploads, ids do not).
    expected_sources: Mapped[list] = json_list()

    results: Mapped[list["EvaluationResult"]] = relationship(
        back_populates="question", cascade="all, delete-orphan", passive_deletes=True
    )


class EvaluationRun(TimestampMixin, Base):
    __tablename__ = "evaluation_runs"
    __table_args__ = (
        CheckConstraint("top_k >= 1", name="top_k_positive"),
        CheckConstraint("question_count >= 0", name="question_count_positive"),
        CheckConstraint(
            "started_at IS NULL OR finished_at IS NULL OR finished_at >= started_at",
            name="times_ordered",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    dataset: Mapped[str] = mapped_column(String(100), default="default", server_default="default")
    status: Mapped[RunStatus] = mapped_column(
        enum_type(RunStatus, "run_status"),
        default=RunStatus.PENDING,
        server_default=RunStatus.PENDING.value,
        index=True,
    )
    # The configuration under test, so two runs can be compared like-for-like.
    retrieval_mode: Mapped[RetrievalMode] = mapped_column(enum_type(RetrievalMode, "retrieval_mode"))
    top_k: Mapped[int] = mapped_column(Integer, default=5, server_default="5")
    llm_model: Mapped[str | None] = mapped_column(String(100))
    embedding_model: Mapped[str | None] = mapped_column(String(200))
    config: Mapped[dict[str, Any]] = json_object()  # chunk size, etc.
    question_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    metrics: Mapped[dict[str, Any]] = json_object()  # aggregates
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    results: Mapped[list["EvaluationResult"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", passive_deletes=True
    )


class EvaluationResult(TimestampMixin, Base):
    __tablename__ = "evaluation_results"
    __table_args__ = (
        UniqueConstraint("run_id", "question_id", name="uq_evaluation_results_run_id_question_id"),
        *(_unit_interval(metric) for metric in _UNIT_METRICS),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("evaluation_runs.id", ondelete="CASCADE"))
    question_id: Mapped[int] = mapped_column(
        ForeignKey("evaluation_questions.id", ondelete="CASCADE"), index=True
    )
    # Ranked retrieval output, best first, and the matching similarity scores.
    retrieved_chunk_ids: Mapped[list] = json_list()
    retrieved_scores: Mapped[list] = json_list()
    answer: Mapped[str | None] = mapped_column(Text)
    hit: Mapped[bool | None] = mapped_column(Boolean)  # an expected source was in the top-k
    reciprocal_rank: Mapped[float | None] = mapped_column(Float)
    precision_at_k: Mapped[float | None] = mapped_column(Float)
    recall_at_k: Mapped[float | None] = mapped_column(Float)
    faithfulness: Mapped[float | None] = mapped_column(Float)
    answer_relevance: Mapped[float | None] = mapped_column(Float)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    failure_type: Mapped[FailureType] = mapped_column(
        enum_type(FailureType, "failure_type"),
        default=FailureType.NONE,
        server_default=FailureType.NONE.value,
        index=True,
    )
    failure_notes: Mapped[str | None] = mapped_column(Text)

    run: Mapped[EvaluationRun] = relationship(back_populates="results")
    question: Mapped[EvaluationQuestion] = relationship(back_populates="results")
