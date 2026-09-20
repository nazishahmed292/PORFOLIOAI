"""Test configuration.

Environment variables are set *before* any `app` module is imported so that the
settings singleton and the database engine pick up the test values. Unit tests
run on in-memory SQLite (fast, no services needed); Postgres-specific behaviour
is covered by the Docker/integration run.
"""

import os

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-that-is-long-enough-for-validation"
os.environ["GEMINI_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database.base import Base  # noqa: E402
from app.database.session import engine  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def client(app):
    # raise_server_exceptions=False lets us assert on the 500 JSON body
    # instead of the test client re-raising the exception.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
