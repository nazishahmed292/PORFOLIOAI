"""SQLAlchemy ORM models.

Every model module is imported here so that Alembic's autogenerate, the schema-drift test
and `Base.metadata.create_all` all see the complete set of tables. Import names from this
package (``from app.models import User``), never from the individual modules.
"""

from app.database.base import Base
from app.models.analysis import JobAnalysis, ResumeAnalysis
from app.models.chat import ChatMessage, ChatSession, MessageCitation
from app.models.column_types import EMBEDDING_DIM
from app.models.document import Document, DocumentChunk
from app.models.enums import (
    DocumentKind,
    DocumentStatus,
    FailureType,
    MessageRole,
    ProjectStatus,
    QuestionCategory,
    RetrievalMode,
    RunStatus,
    SkillCategory,
    UserRole,
)
from app.models.evaluation import EvaluationQuestion, EvaluationResult, EvaluationRun
from app.models.portfolio import Certification, Education, Experience, Project, Skill, project_skills
from app.models.profile import Profile
from app.models.user import User

__all__ = [
    "Base",
    "EMBEDDING_DIM",
    # tables
    "Certification",
    "ChatMessage",
    "ChatSession",
    "Document",
    "DocumentChunk",
    "Education",
    "EvaluationQuestion",
    "EvaluationResult",
    "EvaluationRun",
    "Experience",
    "JobAnalysis",
    "MessageCitation",
    "Profile",
    "Project",
    "ResumeAnalysis",
    "Skill",
    "User",
    "project_skills",
    # enums
    "DocumentKind",
    "DocumentStatus",
    "FailureType",
    "MessageRole",
    "ProjectStatus",
    "QuestionCategory",
    "RetrievalMode",
    "RunStatus",
    "SkillCategory",
    "UserRole",
]
