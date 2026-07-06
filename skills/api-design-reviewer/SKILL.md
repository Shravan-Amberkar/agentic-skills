---
name: api-design-reviewer
description: Use when designing or reviewing an HTTP/REST or gRPC API and you want it to be consistent, evolvable, and safe before it ships. Reviews resource naming and URL structure, HTTP method/status correctness, pagination and filtering, idempotency of writes, error response shape, versioning strategy, auth and rate limiting, and backward compatibility. Recommends REST for public/partner APIs and gRPC for internal service-to-service. Trigger when the user shares an API spec (OpenAPI/proto), endpoint definitions, or asks to design or review an API contract.
license: MIT
---

# API Design Reviewer

Review API designs the way a tech lead would before a public/partner contract is locked. Optimize
for consistency and the ability to evolve without breaking clients.

## When to use
- User shares an OpenAPI/Swagger spec, `.proto`, or endpoint list
- "Design/review this API"
- Deciding REST vs gRPC

## Choosing the style
- **REST/JSON** for public, partner, and browser-facing APIs (discoverable, cacheable, ubiquitous).
- **gRPC** for internal, high-throughput service-to-service calls (typed contracts, streaming, perf).
- **Events (Kafka)** for fire-and-forget, fan-out, and async workflows — not request/response.

## REST checklist
- **Resources, not verbs**: `POST /payments`, `GET /payments/{id}` — not `/createPayment`.
- **Correct methods & status**: 200/201/202/204, 400 vs 422, 401 vs 403, 404, 409 for conflicts, 429.
- **Idempotency**: POST that creates money/side effects should accept an `Idempotency-Key` header and
  dedupe; PUT/DELETE are naturally idempotent.
- **Pagination**: cursor-based for large/append-only sets; document limits and defaults.
- **Filtering/sorting**: consistent query-param conventions; avoid unbounded queries.
- **Error shape**: one consistent envelope (`code`, `message`, `details`, a trace/`request_id`).
- **Versioning**: version in the path (`/v1`) or header; never make breaking changes in place.
- **Consistency**: snake_case or camelCase — pick one; consistent timestamps (RFC3339, UTC); money as
  minor units or decimal strings, never floats.

## gRPC / proto checklist
- Stable field numbers; never reuse or renumber; add, don't repurpose.
- Use `google.protobuf.Timestamp`; avoid bare ints for time/money.
- Design for backward/forward compatibility; mark deprecated fields, don't delete.
- Define clear error model (status codes + error details), deadlines/timeouts, and pagination.

## Cross-cutting
- **Auth**: state the scheme (OAuth2/JWT/mTLS for internal); least privilege; per-key scoping for partners.
- **Rate limiting** and quotas documented with 429 + `Retry-After`.
- **Backward compatibility**: adding optional fields = safe; removing/renaming/retyping = breaking.

## Output
Findings grouped: **Breaking-risk** (will break clients or correctness), **Consistency**, **Nice-to-have**.
For each: the endpoint/field, why it matters, and the corrected design. End with REST-vs-gRPC fit if relevant.
