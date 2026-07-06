---
name: go-microservice-scaffold
description: Use when creating a new Go backend microservice, bootstrapping a Go API, or standardizing an existing Go service to production conventions. Scaffolds an idiomatic layout (cmd/ entrypoint, internal/ packages), 12-factor config loading from env, structured logging with zerolog, context-aware graceful shutdown, liveness/readiness HTTP endpoints, Prometheus /metrics, a multi-stage Dockerfile, and a Makefile. Trigger when the user asks to create, bootstrap, scaffold, or set up a new Go service/API, or to add standard production scaffolding (health checks, metrics, graceful shutdown, Docker) to existing Go code.
license: MIT
---

# Go Microservice Scaffold

Generate a production-ready Go HTTP service that follows conventions proven in high-throughput
fintech systems. Prefer the standard library plus a thin router; avoid heavy frameworks.

## When to use
- "Create/scaffold a new Go service/microservice/API"
- "Set up a Go backend with health checks and metrics"
- "Add graceful shutdown / Prometheus metrics / Docker to my Go service"

## Target layout

```
<service-name>/
├── cmd/<service-name>/main.go     # entrypoint: wire config, server, signals
├── internal/
│   ├── config/config.go           # env-based 12-factor config
│   ├── server/server.go           # http.Server + routes + middleware
│   ├── handler/                   # request handlers
│   └── observability/             # logger + metrics setup
├── Dockerfile                     # multi-stage, distroless/alpine final
├── Makefile                       # build, run, test, lint, docker targets
├── go.mod
└── README.md
```

## Conventions (apply these)

1. **Config** — load from environment with sane defaults; fail fast on missing required vars.
   Expose `PORT`, `LOG_LEVEL`, and any datastore URLs. Never read config outside `internal/config`.
2. **Logging** — `zerolog`, structured JSON in prod, console writer in dev (driven by `LOG_LEVEL`/`ENV`).
   Inject a request-scoped logger via middleware; include a `request_id`.
3. **Graceful shutdown** — listen for `SIGINT`/`SIGTERM`, `server.Shutdown(ctx)` with a timeout
   (default 15s), drain in-flight requests, close datastore pools last.
4. **Health endpoints** — `GET /healthz` (liveness, always 200 once up) and `GET /readyz`
   (readiness, checks datastore pings). Keep them unauthenticated and cheap.
5. **Metrics** — expose Prometheus `GET /metrics` via `promhttp`; add a default histogram for
   HTTP request duration labelled by route, method, status.
6. **HTTP server hardening** — set `ReadHeaderTimeout`, `ReadTimeout`, `WriteTimeout`, `IdleTimeout`.
7. **Dockerfile** — multi-stage: build with `golang:<ver>` (`CGO_ENABLED=0`), final stage on
   `gcr.io/distroless/static` or `alpine`; run as non-root; copy only the binary.
8. **Makefile** — provide `build`, `run`, `test`, `lint` (golangci-lint), `docker-build`, `up`.

## Steps

1. Ask for (or infer) the service name and any datastores (Postgres/Redis/Kafka).
2. Create the layout above. Keep `main.go` thin — it only wires config → observability → server → signals.
3. Generate a minimal but real `/healthz`, `/readyz`, `/metrics`, and one example domain route.
4. Add the Dockerfile, Makefile, `go.mod`, and a README with `make run` / `make docker-build`.
5. Ensure `make build` and `make test` pass before finishing.

## Reference snippet — graceful shutdown in main.go

```go
srv := server.New(cfg, logger)
go func() {
    if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
        logger.Fatal().Err(err).Msg("server failed")
    }
}()

ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
defer stop()
<-ctx.Done()

shutdownCtx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
defer cancel()
if err := srv.Shutdown(shutdownCtx); err != nil {
    logger.Error().Err(err).Msg("graceful shutdown failed")
}
```

Keep the generated code small, idiomatic, and immediately runnable with `make run`.
