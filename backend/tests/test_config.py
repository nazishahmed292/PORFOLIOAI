import pytest
from pydantic import ValidationError

from app.core.config import INSECURE_DEFAULT_JWT_SECRET, Settings


def make(**overrides) -> Settings:
    # _env_file=None ignores any developer .env so tests are deterministic
    return Settings(_env_file=None, **overrides)


def test_cors_origins_are_parsed_and_trimmed():
    settings = make(cors_origins="http://a.com, http://b.com ,,")
    assert settings.cors_origins_list == ["http://a.com", "http://b.com"]


def test_production_rejects_default_jwt_secret():
    with pytest.raises(ValidationError):
        make(environment="production", jwt_secret=INSECURE_DEFAULT_JWT_SECRET)


def test_production_rejects_short_jwt_secret():
    with pytest.raises(ValidationError):
        make(environment="production", jwt_secret="too-short")


def test_production_accepts_strong_jwt_secret():
    settings = make(environment="production", jwt_secret="x" * 40)
    assert settings.is_production


def test_llm_api_key_follows_selected_provider():
    settings = make(llm_provider="openai", openai_api_key="sk-o", gemini_api_key="g-key")
    assert settings.llm_api_key == "sk-o"
    settings = make(llm_provider="gemini", openai_api_key="sk-o", gemini_api_key="g-key")
    assert settings.llm_api_key == "g-key"


def test_upload_limit_in_bytes():
    assert make(max_upload_mb=5).max_upload_bytes == 5 * 1024 * 1024


# --- .env.example must stay correct: students copy it verbatim -----------------

from pathlib import Path  # noqa: E402

ENV_EXAMPLE = Path(__file__).resolve().parents[2] / ".env.example"
# Settings that intentionally have no entry in .env.example (sane fixed defaults).
UNDOCUMENTED = {"app_name", "jwt_algorithm", "upload_dir"}


def test_env_example_parses_without_comment_leaking_into_values():
    settings = Settings(_env_file=ENV_EXAMPLE)
    assert settings.llm_model == ""
    assert settings.vector_db_url == ""
    assert settings.cors_origins_list == ["http://localhost:5173", "http://localhost:3000"]


def test_env_example_documents_every_setting():
    keys = {
        line.split("=", 1)[0].strip().lower()
        for line in ENV_EXAMPLE.read_text().splitlines()
        if "=" in line and not line.lstrip().startswith("#")
    }
    missing = set(Settings.model_fields) - keys - UNDOCUMENTED
    assert not missing, f"Add these to .env.example: {sorted(missing)}"
