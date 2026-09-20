"""Aggregates every route module under the /api prefix."""

from fastapi import APIRouter

from app.api.routes import health

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
# Later phases register: auth, profile, skills, projects, documents, chat, ...
