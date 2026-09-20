"""Health checks. Kept in a service so routes stay thin and this stays testable."""

import logging
import time
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app import __version__
from app.core.config import Settings
from app.schemas.common import ComponentStatus, HealthResponse

logger = logging.getLogger(__name__)


def check_database(db: Session) -> ComponentStatus:
    started = time.perf_counter()
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # any failure means "down"; details go to the log, not the client
        logger.warning("Database health check failed", exc_info=True)
        return ComponentStatus(status="down", detail="Database is unreachable.")
    return ComponentStatus(
        status="up", latency_ms=round((time.perf_counter() - started) * 1000, 2)
    )


def build_health_report(db: Session, settings: Settings) -> HealthResponse:
    database = check_database(db)
    return HealthResponse(
        status="ok" if database.status == "up" else "degraded",
        app=settings.app_name,
        version=__version__,
        environment=settings.environment,
        database=database,
        llm_provider=settings.llm_provider,
        # Only reveal *whether* a key exists, never the key itself.
        llm_configured=bool(settings.llm_api_key),
        vector_store=settings.vector_store,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
