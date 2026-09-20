"""Structured portfolio content: skills, projects, experience, education, certifications."""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Table,
    Text,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.enums import ProjectStatus, SkillCategory
from app.models.column_types import enum_type, json_list

if TYPE_CHECKING:
    from app.models.document import Document

# Many-to-many link. Deleting either side removes only the link row, never the other side.
project_skills = Table(
    "project_skills",
    Base.metadata,
    Column("project_id", ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True, index=True),
)


class Skill(TimestampMixin, Base):
    __tablename__ = "skills"
    __table_args__ = (
        CheckConstraint("slug = lower(slug)", name="slug_lowercase"),
        CheckConstraint("proficiency BETWEEN 1 AND 5", name="proficiency_range"),
        CheckConstraint("years_experience IS NULL OR years_experience >= 0", name="years_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))  # display name, e.g. "PyTorch"
    # Lowercase key ("pytorch"): the unique, case-insensitive identity of the skill.
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    category: Mapped[SkillCategory] = mapped_column(
        enum_type(SkillCategory, "skill_category"),
        default=SkillCategory.OTHER,
        server_default=SkillCategory.OTHER.value,
    )
    proficiency: Mapped[int] = mapped_column(SmallInteger, default=3, server_default="3")  # 1-5
    years_experience: Mapped[float | None] = mapped_column(Float)
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    projects: Mapped[list["Project"]] = relationship(
        secondary=project_skills, back_populates="skills", passive_deletes=True
    )


class Project(TimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("slug = lower(slug)", name="slug_lowercase"),
        CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="dates_ordered",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(150), unique=True, index=True)  # used in URLs
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    highlights: Mapped[list] = json_list()  # bullet points
    status: Mapped[ProjectStatus] = mapped_column(
        enum_type(ProjectStatus, "project_status"),
        default=ProjectStatus.COMPLETED,
        server_default=ProjectStatus.COMPLETED.value,
    )
    repo_url: Mapped[str | None] = mapped_column(String(500))
    demo_url: Mapped[str | None] = mapped_column(String(500))
    image_url: Mapped[str | None] = mapped_column(String(500))
    featured: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    skills: Mapped[list[Skill]] = relationship(
        secondary=project_skills, back_populates="projects", passive_deletes=True
    )
    documents: Mapped[list["Document"]] = relationship(back_populates="project")


class Experience(TimestampMixin, Base):
    __tablename__ = "experiences"
    __table_args__ = (
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="dates_ordered"),
        # A current role cannot also have an end date.
        CheckConstraint("NOT (is_current AND end_date IS NOT NULL)", name="current_has_no_end"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(200))
    location: Mapped[str | None] = mapped_column(String(200))
    employment_type: Mapped[str | None] = mapped_column(String(50))  # internship, full-time...
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    description: Mapped[str | None] = mapped_column(Text)
    achievements: Mapped[list] = json_list()
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class Education(TimestampMixin, Base):
    __tablename__ = "education"
    __table_args__ = (
        CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="dates_ordered",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    institution: Mapped[str] = mapped_column(String(200))
    degree: Mapped[str] = mapped_column(String(200))
    field_of_study: Mapped[str | None] = mapped_column(String(200))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    grade: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class Certification(TimestampMixin, Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    issuer: Mapped[str] = mapped_column(String(200))
    issued_date: Mapped[date | None] = mapped_column(Date)
    credential_url: Mapped[str | None] = mapped_column(String(500))
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
