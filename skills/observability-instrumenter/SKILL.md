---
name: observability-instrumenter
description: Use when a service lacks proper metrics, logs, or traces and you want to add the three pillars of observability without over-instrumenting. Adds Prometheus metrics (RED method - rate, errors, duration), structured logging with correlation/request ids, and OpenTelemetry distributed tracing with context propagation across service and Kafka boundaries. Recommends the key SLI metrics and alert thresholds to watch. Trigger when the user asks to add metrics/logging/tracing, instrument a service, set up Prometheus/Grafana/OpenTelemetry, or debug why they have no visibility into production.
license: MIT
---

# Observability Instrumenter

Add the three pillars — metrics, logs, traces — so a service is debuggable in production. Instrument
what answers real questions; don't bury signal under noise.

## When to use
- "Add metrics/logging/tracing" / "instrument this service"
- "Set up Prometheus / Grafana / OpenTelemetry"
- "I have no visibility into what's happening in prod"

## Metrics — use the RED method
For every request path expose:
- **Rate** — requests per second (counter, labelled by route/method).
- **Errors** — error count/ratio (counter, labelled by route/status class).
- **Duration** — latency histogram (so you can compute P50/P95/P99).

For consumers/queues add **lag**, processed, retried, dead-lettered. For datastores add pool
utilization and query duration. Expose `/metrics` for Prometheus. Avoid high-cardinality labels
(no user ids, no raw paths with ids) — they blow up Prometheus.

## Logs — structured + correlated
- JSON structured logs in production; include `request_id`/`correlation_id`, route, status, latency.
- Propagate the correlation id from inbound request → downstream calls → Kafka headers, so one
  request can be traced across services by id.
- Log levels with intent: error = needs attention; warn = degraded; info = lifecycle; debug = dev only.
- Never log secrets, tokens, full PII, or card/bank numbers.

## Traces — OpenTelemetry
- Auto-instrument HTTP/gRPC server + client; add spans around DB calls, external vendors, and Kafka
  produce/consume. Propagate trace context via W3C `traceparent` (and into Kafka headers).
- Export to an OTLP collector → Tempo/Jaeger. Sample sensibly (e.g. tail-based or a ratio) to control cost.

## SLIs & alerts to recommend
- Availability (success ratio), latency (P99), error rate, saturation (CPU/mem/pool), consumer lag.
- Suggest alert thresholds tied to an SLO (e.g. P99 latency > target for 5m; error rate > 1% for 5m;
  consumer lag growing for 10m).

## Steps
1. Identify language/framework and key paths (HTTP routes, consumers, DB, external vendors).
2. Wire metrics (RED), structured logging with correlation id, and OTel tracing with propagation.
3. Provide a starter Grafana dashboard outline and the alert rules above.
4. Verify `/metrics` scrapes and a trace appears end-to-end before finishing.

Pairs with an `observability-bootstrap` compose stack (Prometheus/Grafana/Loki/Tempo) for local testing.
