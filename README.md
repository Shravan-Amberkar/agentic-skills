# agentic-skills

A collection of reusable **Agent Skills** for backend, infrastructure, and DevOps engineering —
authored to the open [`SKILL.md` standard](https://agenticskills.io). **Install once, use everywhere:**
they work across Claude Code, OpenAI Codex, Cursor, Gemini CLI, GitHub Copilot, Windsurf, Roo Code,
Amp, Goose, and other SKILL.md-compatible agents.

Built by [Shravan Amberkar](https://github.com/Shravan-Amberkar) — distilled from ~7 years of
building and operating a production fintech lending platform (Go, Python/FastAPI, Kafka,
PostgreSQL, AWS). The theme: **make the hard, scary parts of shipping software one step easier** —
service scaffolding, schema review, Kafka consumers, CI, observability, and incident response.

## What's inside

| Skill | What it does |
|---|---|
| [`go-microservice-scaffold`](skills/go-microservice-scaffold) | Scaffold a production-ready Go service (config, graceful shutdown, health, metrics, Docker, Make). |
| [`postgres-schema-reviewer`](skills/postgres-schema-reviewer) | Review migrations & schemas: TIMESTAMPTZ, indexes, naming, unsafe-migration locks. |
| [`kafka-consumer-builder`](skills/kafka-consumer-builder) | Idempotent Kafka consumer/producer with DLQ, retries, and safe consumer-group ids. |
| [`dockerfile-optimizer`](skills/dockerfile-optimizer) | Multi-stage, minimal, non-root, cache-friendly, secure images. |
| [`ci-pipeline-generator`](skills/ci-pipeline-generator) | GitHub Actions + Jenkinsfile with lint/test/build/docker/deploy. |
| [`incident-rca-writer`](skills/incident-rca-writer) | Blameless RCA/postmortem from logs, metrics, and notes. |
| [`api-design-reviewer`](skills/api-design-reviewer) | REST/gRPC API design review: naming, status codes, idempotency, versioning. |
| [`helm-chart-generator`](skills/helm-chart-generator) | Helm chart + per-env values with production defaults. |
| [`observability-instrumenter`](skills/observability-instrumenter) | Prometheus (RED), structured logs, and OpenTelemetry tracing. |
| [`fastapi-service-scaffold`](skills/fastapi-service-scaffold) | Production FastAPI service: app factory, async SQLAlchemy, health, metrics, tests. |
| [`notification-gateway`](skills/notification-gateway) | Send/integrate/migrate/troubleshoot a multi-channel notification gateway (email/SMS/WhatsApp/OTP). |
| [`brms-integration`](skills/brms-integration) | Adopt a BRMS (GoRules Zen Engine): identify rule candidates, build rulesets, integrate the eval API. |
| [`diverge-converge`](skills/diverge-converge) | Guilford-style brainstorm → evaluate: isolated personas diverge, kill gates + weighted rubric converge on ONE winner and a blueprint. A stdlib script does all the scoring arithmetic. |
| [`demo-video-recorder`](skills/demo-video-recorder) | Narrated demo video of any running web app: script → Playwright + offline Kokoro voice + ffmpeg → MP4, with timing check and frame review. |

## Install

Each skill is a self-contained directory under `skills/`. Use any SKILL.md-compatible agent:

```bash
# via the skills CLI
npx skills add Shravan-Amberkar/go-microservice-scaffold

# or clone and point your agent at the skills/ directory
git clone https://github.com/Shravan-Amberkar/agentic-skills.git
```

Or copy a skill directory into your agent's skills folder — it's discovered automatically:

| Agent | Skills folder |
|---|---|
| Claude Code | `~/.claude/skills/` |
| OpenAI Codex | `~/.codex/skills/` |
| Cursor | `.cursor/skills/` |
| Gemini CLI | `~/.gemini/skills/` |
| GitHub Copilot | `.github/skills/` |
| Windsurf | `.windsurf/skills/` |

## The SKILL.md standard

Every skill is a directory containing a `SKILL.md` file with YAML frontmatter:

```yaml
---
name: skill-name            # required · ≤64 chars · lowercase + hyphens
description: ...            # required · ≤1024 chars · what it does + when to use it
license: MIT               # optional
---
```

The `description` is what an agent reads to decide *when* to trigger the skill, so it states both
the capability and the trigger conditions. See the
[open specification](https://agenticskills.io/specification) for details.

## License

MIT © Shravan Amberkar
