"""Enumerations stored in the database.

They are persisted as plain VARCHAR columns guarded by a CHECK constraint
(`native_enum=False`) instead of PostgreSQL ENUM types. Adding a value later is
then an ordinary migration on every database, with no `ALTER TYPE` special case.
"""

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"  # the portfolio owner: full access to the dashboard
    VIEWER = "viewer"  # reserved for read-only accounts


class SkillCategory(StrEnum):
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    ML_AI = "ml_ai"
    DATA = "data"
    DATABASE = "database"
    DEVOPS = "devops"
    TOOL = "tool"
    SOFT_SKILL = "soft_skill"
    OTHER = "other"


class ProjectStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class DocumentKind(StrEnum):
    RESUME = "resume"
    PROJECT_DOC = "project_doc"
    PAPER = "paper"
    CERTIFICATE = "certificate"
    NOTE = "note"
    # Text generated from structured portfolio rows (a project, an experience...)
    # so retrieval has exactly one code path: everything searchable is a Document.
    PORTFOLIO_GENERATED = "portfolio_generated"
    OTHER = "other"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class QuestionCategory(StrEnum):
    FACTUAL = "factual"
    SKILLS = "skills"
    PROJECTS = "projects"
    EXPERIENCE = "experience"
    MULTI_HOP = "multi_hop"
    UNANSWERABLE = "unanswerable"  # the corpus has no answer; the system should decline


class RetrievalMode(StrEnum):
    DENSE = "dense"
    BM25 = "bm25"
    HYBRID = "hybrid"
    HYBRID_RERANK = "hybrid_rerank"


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FailureType(StrEnum):
    NONE = "none"
    RETRIEVAL_MISS = "retrieval_miss"  # the right chunk was never retrieved
    RANKING_ERROR = "ranking_error"  # retrieved, but ranked too low to be used
    HALLUCINATION = "hallucination"  # the answer states things the sources do not support
    INCOMPLETE_ANSWER = "incomplete_answer"
    FALSE_REFUSAL = "false_refusal"  # declined although the answer was in the corpus
    MISSED_REFUSAL = "missed_refusal"  # answered an unanswerable question
