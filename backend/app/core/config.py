"""Application settings.

All configuration comes from environment variables (or a local `.env` file).
Nothing secret is hard-coded. Use `get_settings()` everywhere instead of
instantiating `Settings` directly, so the values are parsed once and can be
overridden in tests.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The repo root holds the shared .env used by both Docker and local runs.
REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]

INSECURE_DEFAULT_JWT_SECRET = "change-me-in-development-only"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Later files win: backend/.env overrides the repo-level .env.
        env_file=(REPO_ROOT / ".env", BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application -------------------------------------------------------
    app_name: str = "PortfolioAI"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    # --- Database ----------------------------------------------------------
    database_url: str = (
        "postgresql+psycopg://portfolioai:portfolioai@localhost:5432/portfolioai"
    )

    # --- Security ----------------------------------------------------------
    jwt_secret: str = INSECURE_DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=60 * 12, ge=1)
    # Comma-separated list, e.g. "http://localhost:5173,https://me.dev"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # --- AI providers (all optional until Phase 6) -------------------------
    llm_provider: Literal["openai", "gemini"] = "gemini"
    openai_api_key: str = ""
    gemini_api_key: str = ""
    llm_model: str = ""  # empty -> provider default is chosen in the RAG layer

    # --- Embeddings / vector store ----------------------------------------
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_store: Literal["pgvector", "chroma", "faiss"] = "pgvector"
    vector_db_url: str = ""  # only used by external stores (e.g. a Chroma server)

    # --- Uploads -----------------------------------------------------------
    upload_dir: Path = REPO_ROOT / "data" / "uploads"
    max_upload_mb: int = Field(default=10, ge=1, le=100)

    # --- Derived helpers ---------------------------------------------------
    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def llm_api_key(self) -> str:
        """API key for the currently selected provider (may be empty)."""
        return self.openai_api_key if self.llm_provider == "openai" else self.gemini_api_key

    @model_validator(mode="after")
    def _reject_insecure_production_config(self) -> "Settings":
        if self.is_production and (
            self.jwt_secret == INSECURE_DEFAULT_JWT_SECRET or len(self.jwt_secret) < 32
        ):
            raise ValueError(
                "JWT_SECRET must be set to a random string of at least 32 characters "
                "when ENVIRONMENT=production."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
