---
name: dockerfile-optimizer
description: Use when writing or improving a Dockerfile for a Go, Python, or Node service and you want a small, fast-building, secure image. Applies multi-stage builds, minimal final base images (distroless or alpine), non-root users, build-cache-friendly layer ordering, .dockerignore, pinned versions, and healthchecks. Flags common problems: running as root, copying the whole context, missing layer caching, fat images, secrets baked into layers, and using latest tags. Trigger when the user shares a Dockerfile, asks to containerize a service, or asks why their image is large/slow to build.
license: MIT
---

# Dockerfile Optimizer

Produce production Docker images that are small, reproducible, cache-efficient, and secure.

## When to use
- "Write/optimize a Dockerfile" or "containerize this service"
- "My image is huge / builds slowly"
- Reviewing an existing Dockerfile

## Principles (apply these)

1. **Multi-stage build.** Compile/install in a builder stage; copy only artifacts into a slim final stage.
2. **Minimal final base.** Go → `gcr.io/distroless/static` or `scratch`; Python → `python:*-slim`;
   Node → `node:*-slim` or distroless. Never ship the full SDK image.
3. **Non-root.** Create and `USER` a non-root user in the final stage. Distroless `:nonroot` works for Go.
4. **Cache-friendly layer order.** Copy dependency manifests (`go.mod/go.sum`, `requirements.txt`,
   `package.json/lock`) and download deps *before* copying source, so code changes don't bust the dep cache.
5. **`.dockerignore`.** Exclude `.git`, build output, `node_modules`, env files, test data — keeps the
   build context (and secret-leak risk) small.
6. **Pin versions.** Pin base image tags (and digests for prod); never `latest`.
7. **No secrets in layers.** Use build args/secrets mounts, not `COPY .env`. Secrets in any layer
   persist in history even if later removed.
8. **Healthcheck + metadata.** Add a `HEALTHCHECK` and OCI labels where useful.
9. **Reproducibility.** For Go set `CGO_ENABLED=0`; strip with `-ldflags="-s -w"`.

## Reference — Go multi-stage
```dockerfile
FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /app ./cmd/service

FROM gcr.io/distroless/static:nonroot
COPY --from=build /app /app
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/app"]
```

## Output
When reviewing, list issues by impact (security → size → build speed), then provide the rewritten
Dockerfile and a matching `.dockerignore`. State the expected before/after image size if known.
