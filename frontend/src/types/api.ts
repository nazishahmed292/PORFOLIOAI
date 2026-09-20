/** Shapes returned by the FastAPI backend. Keep in sync with backend/app/schemas. */

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

export interface ComponentStatus {
  status: "up" | "down";
  latency_ms: number | null;
  detail: string | null;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  app: string;
  version: string;
  environment: string;
  database: ComponentStatus;
  llm_provider: string;
  llm_configured: boolean;
  vector_store: string;
  timestamp: string;
}
