"""Schemas shared by many endpoints."""

from typing import Any, Literal

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    """Shape of every error returned by the API (see app/core/errors.py)."""

    error: ErrorBody


class ComponentStatus(BaseModel):
    status: Literal["up", "down"]
    latency_ms: float | None = None
    detail: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    app: str
    version: str
    environment: str
    database: ComponentStatus
    llm_provider: str
    llm_configured: bool
    vector_store: str
    timestamp: str
