from sqlalchemy.exc import OperationalError

from app.database.session import get_db


def test_liveness(client):
    response = client.get("/api/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_reports_database_up(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"]["status"] == "up"
    assert body["database"]["latency_ms"] is not None
    assert body["app"] == "PortfolioAI"
    assert body["environment"] == "test"


def test_health_never_leaks_api_keys(client):
    body = client.get("/api/health").json()
    assert body["llm_configured"] is False  # no key in the test environment
    assert "api_key" not in str(body).lower()


def test_health_degraded_when_database_down(app, client):
    class BrokenSession:
        def execute(self, *_args, **_kwargs):
            raise OperationalError("SELECT 1", {}, Exception("connection refused"))

        def close(self):
            pass

    app.dependency_overrides[get_db] = lambda: BrokenSession()
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["database"]["status"] == "down"
    assert "connection refused" not in response.text  # internal detail is not exposed


def test_response_has_request_id_header(client):
    response = client.get("/api/health/live")
    assert response.headers.get("x-request-id")

    echoed = client.get("/api/health/live", headers={"X-Request-ID": "abc123"})
    assert echoed.headers["x-request-id"] == "abc123"
