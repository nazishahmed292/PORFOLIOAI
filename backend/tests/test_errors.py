"""The API must always answer errors in one consistent JSON shape."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.errors import ConflictError, NotFoundError


def _add_test_routes(app):
    router = APIRouter()

    class Payload(BaseModel):
        name: str = Field(min_length=2)
        age: int

    @router.get("/_test/not-found")
    def not_found():
        raise NotFoundError("Project not found")

    @router.get("/_test/conflict")
    def conflict():
        raise ConflictError("Email already registered", details={"field": "email"})

    @router.post("/_test/validate")
    def validate(payload: Payload):
        return payload

    @router.get("/_test/boom")
    def boom():
        raise RuntimeError("secret internal detail: db password is hunter2")

    app.include_router(router)


def test_app_error_shape(app, client):
    _add_test_routes(app)
    response = client.get("/_test/not-found")
    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "not_found", "message": "Project not found", "details": None}
    }


def test_app_error_details(app, client):
    _add_test_routes(app)
    response = client.get("/_test/conflict")
    assert response.status_code == 409
    assert response.json()["error"]["details"] == {"field": "email"}


def test_validation_error_lists_fields(app, client):
    _add_test_routes(app)
    response = client.post("/_test/validate", json={"name": "x"})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    fields = {item["field"] for item in error["details"]}
    assert fields == {"name", "age"}


def test_unknown_route_uses_error_shape(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_method_not_allowed_uses_error_shape(client):
    response = client.post("/api/health/live")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_unhandled_exception_hides_internals(app, client):
    _add_test_routes(app)
    response = client.get("/_test/boom")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "hunter2" not in response.text
    assert "Traceback" not in response.text
