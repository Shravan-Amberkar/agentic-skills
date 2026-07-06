---
name: ci-pipeline-generator
description: Use when setting up CI/CD for a service and you want a working pipeline without learning every detail of the CI system. Generates a GitHub Actions workflow and/or a Jenkinsfile tailored to the repo (Go, Python, or Node) covering lint, test with coverage, build, Docker image build and push, and an optional deploy stage. Includes dependency caching, matrix where useful, branch protections, and secret references done safely. Trigger when the user asks to set up CI, add a GitHub Actions workflow or Jenkinsfile, add a build/test/deploy pipeline, or containerize-and-publish on push.
license: MIT
---

# CI Pipeline Generator

Generate a CI/CD pipeline that runs green on first push. Default to **GitHub Actions**; also produce
a **Jenkinsfile** when the user's org uses Jenkins. Keep stages explicit and fast.

## When to use
- "Set up CI / add a pipeline / GitHub Actions / Jenkinsfile"
- "Build and push a Docker image on push/tag"
- "Add lint + test + coverage gates"

## Pipeline shape (adapt to language)
1. **Setup** — checkout, set up toolchain (Go/Python/Node), restore dependency cache.
2. **Lint** — `golangci-lint` / `ruff` + `mypy` / `eslint`. Fail on errors.
3. **Test** — run unit tests with race detector (Go `-race`) and coverage; upload coverage artifact.
4. **Build** — compile / package.
5. **Docker** — build image, tag with git SHA + branch/tag, push to registry (only on main/tags).
6. **Deploy (optional)** — gated on environment; apply Helm/manifests or trigger a deploy.

## Rules
- **Cache dependencies** (Go module cache, pip/uv, npm) keyed on the lockfile hash.
- **Pin action versions** (e.g. `actions/checkout@v4`) and tool versions.
- **Least-privilege secrets** — reference `secrets.*` / Jenkins credentials; never echo them. Scope
  registry/deploy creds to the jobs that need them.
- **Fast feedback** — run lint+test on every PR; build+push only on `main`/tags.
- **Branch protection** — note required status checks to enable on the default branch.

## Reference — GitHub Actions (Go)
```yaml
name: ci
on: { push: { branches: [main] }, pull_request: {} }
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with: { go-version: '1.22', cache: true }
      - run: go vet ./...
      - run: go test -race -coverprofile=cover.out ./...
  docker:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/build-push-action@v6
        with: { push: true, tags: "ghcr.io/${{ github.repository }}:${{ github.sha }}" }
```

## Output
Ask for: language, registry, and whether they deploy from CI. Then emit the workflow file(s) and a
short note on which secrets/branch-protection rules to configure. Pairs well with `dockerfile-optimizer`
and `helm-chart-generator`.
