"""Results of the owner's job-description and resume analyzers (Phase 9)."""

from typing import Any

from sqlalchemy import CheckConstraint, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin
from app.models.column_types import json_list


class JobAnalysis(TimestampMixin, Base):
    __tablename__ = "job_analyses"
    __table_args__ = (CheckConstraint("match_score BETWEEN 0 AND 100", name="score_range"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    job_title: Mapped[str] = mapped_column(String(255))
    company: Mapped[str | None] = mapped_column(String(255))
    job_description: Mapped[str] = mapped_column(Text)
    match_score: Mapped[float] = mapped_column(Float)  # 0-100
    summary: Mapped[str | None] = mapped_column(Text)
    matched_skills: Mapped[list] = json_list()
    missing_skills: Mapped[list] = json_list()
    recommendations: Mapped[list] = json_list()
    # Portfolio chunks that back the match, as [{"chunk_id": 1, "title": "...", "score": 0.8}].
    evidence: Mapped[list[dict[str, Any]]] = json_list()
    model: Mapped[str | None] = mapped_column(String(100))


class ResumeAnalysis(TimestampMixin, Base):
    __tablename__ = "resume_analyses"
    __table_args__ = (CheckConstraint("overall_score BETWEEN 0 AND 100", name="score_range"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    filename: Mapped[str | None] = mapped_column(String(255))
    target_role: Mapped[str | None] = mapped_column(String(255))
    resume_text: Mapped[str] = mapped_column(Text)
    overall_score: Mapped[float] = mapped_column(Float)  # 0-100
    strengths: Mapped[list] = json_list()
    gaps: Mapped[list] = json_list()
    suggestions: Mapped[list] = json_list()
    model: Mapped[str | None] = mapped_column(String(100))
