---
name: fastapi-service-scaffold
description: Use when creating a new Python FastAPI service or standardizing an existing one to production conventions. Scaffolds a clean layout (app factory, routers, dependencies, settings via pydantic-settings), async SQLAlchemy 2.0 with a session dependency, structured logging, lifespan-based startup/shutdown, health/readiness endpoints, Prometheus metrics, Dockerfile, and tests with pytest + httpx. Trigger when the user asks to create, bootstrap, or scaffold a FastAPI service/API, or to add production structure (config, async DB, health checks, metrics, tests) to existing FastAPI code.
license: MIT
---

# FastAPI Service Scaffold

Generate a production-ready FastAPI service with async-first conventions. Keep it clean and testable;
avoid dumping everything in one `main.py`.

## When to use
- "Create/scaffold a FastAPI service/API"
- "Add structure / async DB / health checks / tests to my FastAPI app"

## Target layout
```
<service>/
├── app/
│   ├── main.py              # create_app() factory + lifespan
│   ├── config.py            # pydantic-settings (env-driven)
│   ├── api/                 # routers (versioned, e.g. api/v1/)
│   ├── deps.py              # dependencies (db session, auth)
│   ├── db.py                # async engine + session factory
│   ├── models/             # SQLAlchemy 2.0 models
│   ├── schemas/            # pydantic request/response models
│   └── observability.py     # logging + metrics
├── tests/                  # pytest + httpx AsyncClient
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Conventions (apply these)
1. **App factory** — `create_app()` wires routers, middleware, and a `lifespan` context that opens
   the DB pool on startup and disposes it on shutdown. No module-level side effects.
2. **Settings** — `pydantic-settings` `BaseSettings` reading env; one `Settings` instance via a cached
   dependency. Fail fast on missing required vars.
3. **Async DB** — SQLAlchemy 2.0 async engine + `async_sessionmaker`; provide an `AsyncSession`
   dependency; one session per request, committed/rolled back at the edge.
4. **Schemas vs models** — pydantic schemas for I/O, SQLAlchemy models for persistence; never leak
   ORM objects directly in responses.
5. **Health** — `GET /healthz` (liveness) and `GET /readyz` (DB ping). Unauthenticated and cheap.
6. **Metrics** — Prometheus via `prometheus-fastapi-instrumentator` or custom middleware (RED metrics).
7. **Logging** — structured (structlog or stdlib JSON) with a `request_id` middleware.
8. **Errors** — consistent exception handlers returning a uniform error envelope.
9. **Tests** — `pytest` + `httpx.AsyncClient` against the app; a fixture for a test DB/session.
10. **Tooling** — `ruff` (lint+format) and `mypy`; `uv` or `pip-tools` for deps; pin versions.

## Steps
1. Ask for service name and datastores (Postgres assumed; Redis/Kafka optional).
2. Generate the layout with an app factory, settings, async DB session dep, health, metrics, and one
   example router with a schema and a test.
3. Add Dockerfile (slim Python multi-stage, non-root) and README with `uvicorn app.main:create_app --factory`.
4. Ensure `pytest` and `ruff check` pass before finishing.

Mirrors `go-microservice-scaffold` so Go and Python services in the same org feel consistent.
