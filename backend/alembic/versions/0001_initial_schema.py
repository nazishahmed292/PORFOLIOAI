"""initial schema

Creates every table of the application. Runs unchanged on PostgreSQL (production:
pgvector + JSONB + native UUID) and on SQLite (fast local tests: JSON fallbacks).

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import VECTOR
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Frozen copy of app.models.column_types.EMBEDDING_DIM at the time of this migration.
EMBEDDING_DIM = 384


def _json() -> sa.types.TypeEngine:
    return sa.JSON(none_as_null=True).with_variant(
        postgresql.JSONB(none_as_null=True), "postgresql"
    )


def _embedding() -> sa.types.TypeEngine:
    return VECTOR(EMBEDDING_DIM).with_variant(sa.JSON(none_as_null=True), "sqlite")


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if _is_postgres():
        # Also done by docker/postgres/init.sql; repeating it makes the migration work
        # against any PostgreSQL that has pgvector installed.
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "certifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("issuer", sa.String(length=200), nullable=False),
        sa.Column("issued_date", sa.Date(), nullable=True),
        sa.Column("credential_url", sa.String(length=500), nullable=True),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_certifications")),
    )
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("visitor_id", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_sessions")),
    )
    op.create_index(
        op.f("ix_chat_sessions_visitor_id"),
        "chat_sessions",
        ["visitor_id"],
        unique=False,
    )
    op.create_table(
        "education",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("institution", sa.String(length=200), nullable=False),
        sa.Column("degree", sa.String(length=200), nullable=False),
        sa.Column("field_of_study", sa.String(length=200), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("grade", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name=op.f("ck_education_dates_ordered"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_education")),
    )
    op.create_table(
        "evaluation_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "dataset", sa.String(length=100), server_default="default", nullable=False
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("ground_truth", sa.Text(), nullable=True),
        sa.Column(
            "category",
            sa.Enum(
                "factual",
                "skills",
                "projects",
                "experience",
                "multi_hop",
                "unanswerable",
                name="question_category",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="factual",
            nullable=False,
        ),
        sa.Column(
            "is_answerable", sa.Boolean(), server_default=sa.true(), nullable=False
        ),
        sa.Column("expected_sources", _json(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluation_questions")),
    )
    op.create_index(
        op.f("ix_evaluation_questions_dataset"),
        "evaluation_questions",
        ["dataset"],
        unique=False,
    )
    op.create_table(
        "experiences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("employment_type", sa.String(length=50), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "is_current", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("achievements", _json(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "NOT (is_current AND end_date IS NOT NULL)",
            name=op.f("ck_experiences_current_has_no_end"),
        ),
        sa.CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name=op.f("ck_experiences_dates_ordered"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_experiences")),
    )
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=150), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("highlights", _json(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "planned",
                "in_progress",
                "completed",
                "archived",
                name="project_status",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="completed",
            nullable=False,
        ),
        sa.Column("repo_url", sa.String(length=500), nullable=True),
        sa.Column("demo_url", sa.String(length=500), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("featured", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name=op.f("ck_projects_dates_ordered"),
        ),
        sa.CheckConstraint(
            "slug = lower(slug)", name=op.f("ck_projects_slug_lowercase")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
    )
    op.create_index(op.f("ix_projects_slug"), "projects", ["slug"], unique=True)
    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "language",
                "framework",
                "ml_ai",
                "data",
                "database",
                "devops",
                "tool",
                "soft_skill",
                "other",
                name="skill_category",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="other",
            nullable=False,
        ),
        sa.Column("proficiency", sa.SmallInteger(), server_default="3", nullable=False),
        sa.Column("years_experience", sa.Float(), nullable=True),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "proficiency BETWEEN 1 AND 5", name=op.f("ck_skills_proficiency_range")
        ),
        sa.CheckConstraint("slug = lower(slug)", name=op.f("ck_skills_slug_lowercase")),
        sa.CheckConstraint(
            "years_experience IS NULL OR years_experience >= 0",
            name=op.f("ck_skills_years_positive"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_skills")),
    )
    op.create_index(op.f("ix_skills_slug"), "skills", ["slug"], unique=True)
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "admin",
                "viewer",
                name="user_role",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="admin",
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "email = lower(email)", name=op.f("ck_users_email_lowercase")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "user",
                "assistant",
                "system",
                name="message_role",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("is_grounded", sa.Boolean(), nullable=True),
        sa.Column("feedback", sa.SmallInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "feedback IS NULL OR feedback IN (-1, 1)",
            name=op.f("ck_chat_messages_feedback_values"),
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["chat_sessions.id"],
            name=op.f("fk_chat_messages_session_id_chat_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_messages")),
    )
    op.create_index(
        "ix_chat_messages_session_id_created_at",
        "chat_messages",
        ["session_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("stored_path", sa.String(length=500), nullable=True),
        sa.Column("content_type", sa.String(length=100), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column(
            "kind",
            sa.Enum(
                "resume",
                "project_doc",
                "paper",
                "certificate",
                "note",
                "portfolio_generated",
                "other",
                name="document_kind",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="other",
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "uploaded",
                "processing",
                "ready",
                "failed",
                name="document_status",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="uploaded",
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_public", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "chunk_count >= 0", name=op.f("ck_documents_chunk_count_positive")
        ),
        sa.CheckConstraint(
            "file_size_bytes IS NULL OR file_size_bytes >= 0",
            name=op.f("ck_documents_size_positive"),
        ),
        sa.CheckConstraint(
            "sha256 IS NULL OR length(sha256) = 64",
            name=op.f("ck_documents_sha256_length"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_documents_owner_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_documents_project_id_projects"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
        sa.UniqueConstraint("sha256", name=op.f("uq_documents_sha256")),
    )
    op.create_index(
        op.f("ix_documents_owner_id"), "documents", ["owner_id"], unique=False
    )
    op.create_index(
        op.f("ix_documents_project_id"), "documents", ["project_id"], unique=False
    )
    op.create_index(op.f("ix_documents_status"), "documents", ["status"], unique=False)
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column(
            "dataset", sa.String(length=100), server_default="default", nullable=False
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "completed",
                "failed",
                name="run_status",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "retrieval_mode",
            sa.Enum(
                "dense",
                "bm25",
                "hybrid",
                "hybrid_rerank",
                name="retrieval_mode",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("top_k", sa.Integer(), server_default="5", nullable=False),
        sa.Column("llm_model", sa.String(length=100), nullable=True),
        sa.Column("embedding_model", sa.String(length=200), nullable=True),
        sa.Column("config", _json(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("question_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("metrics", _json(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "question_count >= 0",
            name=op.f("ck_evaluation_runs_question_count_positive"),
        ),
        sa.CheckConstraint(
            "started_at IS NULL OR finished_at IS NULL OR finished_at >= started_at",
            name=op.f("ck_evaluation_runs_times_ordered"),
        ),
        sa.CheckConstraint(
            "top_k >= 1", name=op.f("ck_evaluation_runs_top_k_positive")
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_evaluation_runs_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluation_runs")),
    )
    op.create_index(
        op.f("ix_evaluation_runs_created_by"),
        "evaluation_runs",
        ["created_by"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evaluation_runs_status"), "evaluation_runs", ["status"], unique=False
    )
    op.create_table(
        "job_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("job_title", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("job_description", sa.Text(), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("matched_skills", _json(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("missing_skills", _json(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("recommendations", _json(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("evidence", _json(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "match_score BETWEEN 0 AND 100", name=op.f("ck_job_analyses_score_range")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_job_analyses_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_analyses")),
    )
    op.create_index(
        op.f("ix_job_analyses_user_id"), "job_analyses", ["user_id"], unique=False
    )
    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("headline", sa.String(length=255), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("public_email", sa.String(length=320), nullable=True),
        sa.Column("github_url", sa.String(length=500), nullable=True),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("website_url", sa.String(length=500), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column(
            "open_to_work", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_profiles_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_profiles")),
    )
    op.create_index(op.f("ix_profiles_user_id"), "profiles", ["user_id"], unique=True)
    op.create_table(
        "project_skills",
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_project_skills_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skills.id"],
            name=op.f("fk_project_skills_skill_id_skills"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "project_id", "skill_id", name=op.f("pk_project_skills")
        ),
    )
    op.create_index(
        op.f("ix_project_skills_skill_id"), "project_skills", ["skill_id"], unique=False
    )
    op.create_table(
        "resume_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=True),
        sa.Column("target_role", sa.String(length=255), nullable=True),
        sa.Column("resume_text", sa.Text(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("strengths", _json(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("gaps", _json(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("suggestions", _json(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "overall_score BETWEEN 0 AND 100",
            name=op.f("ck_resume_analyses_score_range"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_resume_analyses_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_resume_analyses")),
    )
    op.create_index(
        op.f("ix_resume_analyses_user_id"), "resume_analyses", ["user_id"], unique=False
    )
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section_title", sa.String(length=255), nullable=True),
        sa.Column("metadata", _json(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("embedding", _embedding(), nullable=True),
        sa.Column("embedding_model", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "chunk_index >= 0", name=op.f("ck_document_chunks_index_positive")
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_document_chunks_document_id_documents"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_chunks")),
        sa.UniqueConstraint(
            "document_id", "chunk_index", name=op.f("uq_document_chunks_document_id_chunk_index")
        ),
    )
    if _is_postgres():
        # Approximate nearest-neighbour index for cosine similarity search.
        op.create_index(
            "ix_document_chunks_embedding_hnsw",
            "document_chunks",
            ["embedding"],
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        )
    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("retrieved_chunk_ids", _json(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("retrieved_scores", _json(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("hit", sa.Boolean(), nullable=True),
        sa.Column("reciprocal_rank", sa.Float(), nullable=True),
        sa.Column("precision_at_k", sa.Float(), nullable=True),
        sa.Column("recall_at_k", sa.Float(), nullable=True),
        sa.Column("faithfulness", sa.Float(), nullable=True),
        sa.Column("answer_relevance", sa.Float(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "failure_type",
            sa.Enum(
                "none",
                "retrieval_miss",
                "ranking_error",
                "hallucination",
                "incomplete_answer",
                "false_refusal",
                "missed_refusal",
                name="failure_type",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="none",
            nullable=False,
        ),
        sa.Column("failure_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "answer_relevance IS NULL OR (answer_relevance >= 0 AND answer_relevance <= 1)",
            name=op.f("ck_evaluation_results_answer_relevance_range"),
        ),
        sa.CheckConstraint(
            "faithfulness IS NULL OR (faithfulness >= 0 AND faithfulness <= 1)",
            name=op.f("ck_evaluation_results_faithfulness_range"),
        ),
        sa.CheckConstraint(
            "precision_at_k IS NULL OR (precision_at_k >= 0 AND precision_at_k <= 1)",
            name=op.f("ck_evaluation_results_precision_at_k_range"),
        ),
        sa.CheckConstraint(
            "recall_at_k IS NULL OR (recall_at_k >= 0 AND recall_at_k <= 1)",
            name=op.f("ck_evaluation_results_recall_at_k_range"),
        ),
        sa.CheckConstraint(
            "reciprocal_rank IS NULL OR (reciprocal_rank >= 0 AND reciprocal_rank <= 1)",
            name=op.f("ck_evaluation_results_reciprocal_rank_range"),
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["evaluation_questions.id"],
            name=op.f("fk_evaluation_results_question_id_evaluation_questions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["evaluation_runs.id"],
            name=op.f("fk_evaluation_results_run_id_evaluation_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluation_results")),
        sa.UniqueConstraint(
            "run_id", "question_id", name=op.f("uq_evaluation_results_run_id_question_id")
        ),
    )
    op.create_index(
        op.f("ix_evaluation_results_failure_type"),
        "evaluation_results",
        ["failure_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evaluation_results_question_id"),
        "evaluation_results",
        ["question_id"],
        unique=False,
    )
    op.create_table(
        "message_citations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.Integer(), nullable=True),
        sa.Column("marker", sa.SmallInteger(), nullable=False),
        sa.Column("source_title", sa.String(length=255), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "marker >= 1", name=op.f("ck_message_citations_marker_positive")
        ),
        sa.ForeignKeyConstraint(
            ["chunk_id"],
            ["document_chunks.id"],
            name=op.f("fk_message_citations_chunk_id_document_chunks"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["chat_messages.id"],
            name=op.f("fk_message_citations_message_id_chat_messages"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_message_citations")),
        sa.UniqueConstraint(
            "message_id", "marker", name=op.f("uq_message_citations_message_id_marker")
        ),
    )
    op.create_index(
        op.f("ix_message_citations_chunk_id"),
        "message_citations",
        ["chunk_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_message_citations_chunk_id"), table_name="message_citations")
    op.drop_table("message_citations")
    op.drop_index(
        op.f("ix_evaluation_results_question_id"), table_name="evaluation_results"
    )
    op.drop_index(
        op.f("ix_evaluation_results_failure_type"), table_name="evaluation_results"
    )
    op.drop_table("evaluation_results")
    if _is_postgres():
        op.drop_index("ix_document_chunks_embedding_hnsw", table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_index(op.f("ix_resume_analyses_user_id"), table_name="resume_analyses")
    op.drop_table("resume_analyses")
    op.drop_index(op.f("ix_project_skills_skill_id"), table_name="project_skills")
    op.drop_table("project_skills")
    op.drop_index(op.f("ix_profiles_user_id"), table_name="profiles")
    op.drop_table("profiles")
    op.drop_index(op.f("ix_job_analyses_user_id"), table_name="job_analyses")
    op.drop_table("job_analyses")
    op.drop_index(op.f("ix_evaluation_runs_status"), table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_created_by"), table_name="evaluation_runs")
    op.drop_table("evaluation_runs")
    op.drop_index(op.f("ix_documents_status"), table_name="documents")
    op.drop_index(op.f("ix_documents_project_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_owner_id"), table_name="documents")
    op.drop_table("documents")
    op.drop_index("ix_chat_messages_session_id_created_at", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_skills_slug"), table_name="skills")
    op.drop_table("skills")
    op.drop_index(op.f("ix_projects_slug"), table_name="projects")
    op.drop_table("projects")
    op.drop_table("experiences")
    op.drop_index(
        op.f("ix_evaluation_questions_dataset"), table_name="evaluation_questions"
    )
    op.drop_table("evaluation_questions")
    op.drop_table("education")
    op.drop_index(op.f("ix_chat_sessions_visitor_id"), table_name="chat_sessions")
    op.drop_table("chat_sessions")
    op.drop_table("certifications")
