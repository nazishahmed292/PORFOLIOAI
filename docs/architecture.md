# Architecture notes

These are the rules the codebase follows, and the reasoning behind them. They are written so you can
explain the design out loud.

## Layers (backend)

```
HTTP request
   │
   ▼
api/routes      Parse the request, call a service, return a schema. No business logic.
   │
   ▼
services        Business rules and orchestration. The only layer that talks to models and the RAG code.
   │
   ├──► models      SQLAlchemy tables (database shape)
   ├──► rag         Chunking, embeddings, retrieval, generation
   └──► evaluation  Metrics and failure analysis

schemas         Pydantic models: the public contract of the API. Never expose ORM models directly.
core            Settings, logging, errors, security. Depends on nothing else in the app.
```

**Why:** each layer can be tested alone. A route test does not need an LLM; a retrieval test does not need
HTTP. Swapping the LLM provider or vector store only touches `rag/`.

## Request lifecycle

1. `RequestContextMiddleware` assigns an `X-Request-ID` and logs the request when it finishes.
2. CORS middleware checks the origin against `CORS_ORIGINS`.
3. The router validates input with Pydantic. Invalid input becomes a `422` in the standard error shape.
4. A dependency supplies one database session per request and always closes it.
5. Exceptions are converted to the standard error shape by handlers in `core/errors.py`.

## Error contract

Every failure returns `{"error": {"code", "message", "details"}}`.

- **Expected failures** raise an `AppError` subclass (`NotFoundError`, `ConflictError`, ...) with a message that
  is safe to show a user.
- **Unexpected failures** (bugs, database errors) are logged with the full stack trace on the server and reach
  the client only as a generic message. Internals such as SQL, file paths or secrets never leave the server.

## Configuration

One `Settings` class (`core/config.py`) reads environment variables and the repo-level `.env`. Rules:

- Nothing secret has a real default. The only default secret is a development placeholder, and
  `ENVIRONMENT=production` refuses to start with it.
- Missing AI keys are a warning at startup, not a crash. Portfolio features keep working; AI endpoints will
  return a clear "not configured" error.
- `.env.example` must list every setting. A test enforces this.

## Database

- SQLAlchemy 2.0 declarative models share one `Base` with a naming convention for constraints, so Alembic
  migrations are deterministic.
- Schema changes are made only through Alembic migrations, never by `create_all` in production. The Docker
  backend runs `alembic upgrade head` before it starts. `alembic check` (also run in the tests) fails if a model
  changes without a migration.
- The full schema, relationships and design decisions are in [database.md](database.md).
- The Compose database image is `pgvector/pgvector`, and `docker/postgres/init.sql` enables the `vector`
  extension. If pgvector is unavailable, the vector store is switchable (`VECTOR_STORE=chroma|faiss`) without
  changing the rest of the app.

## Frontend

- **Routing:** `src/routes.tsx` is the single route table. `PublicLayout` wraps the visitor site,
  `DashboardLayout` wraps owner screens.
- **Server data:** TanStack Query handles fetching, caching and polling. Components never call `fetch`.
- **API client:** `services/api.ts` is the only place that talks to the network. It attaches the JWT, and it
  converts every failure (server errors and an unreachable server) into one `ApiError` type.
- **Styling:** design tokens (colour, radius, fonts) are CSS variables in `index.css`; light and dark themes
  swap the variables. Components use Tailwind utilities against those tokens.
- **Same-origin API:** the browser always calls `/api/...`. Vite (development) and nginx (production) forward
  it to FastAPI, so the app needs no cross-origin setup in normal use.

## Testing strategy

| Level | Tooling | What it covers |
| ----- | ------- | -------------- |
| Backend unit and API | pytest, FastAPI TestClient, in-memory SQLite | Config rules, error shapes, health, later: CRUD, chunking, metrics |
| Frontend | Vitest, Testing Library | Routes render, navigation, theme, API client, health UI states |
| Schema | pytest, real Alembic migration, SQLite and PostgreSQL + pgvector | Constraints, cascades, migration up/down, drift, vector search |
