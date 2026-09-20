from fastapi import APIRouter

from app.api.deps import AppSettings, DbSession
from app.schemas.common import HealthResponse
from app.services.health import build_health_report

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", summary="Liveness probe (no dependencies checked)")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("", response_model=HealthResponse, summary="Service and dependency status")
def health(db: DbSession, settings: AppSettings) -> HealthResponse:
    return build_health_report(db, settings)
