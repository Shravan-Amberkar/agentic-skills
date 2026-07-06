---
name: brms-integration
description: Helps engineering teams adopt a BRMS (Business Rules Management System) built on the GoRules Zen Engine — moving hardcoded business logic into versioned, externally-managed decision tables. Five modes — IDENTIFY (scan a codebase for if/elif threshold logic, fee slabs, and rate tiers that belong in rules), BUILD (create a ruleset via guided UI steps or generated JDM JSON), INTEGRATE (drop a typed evaluation-API client into Python/Go/Node code), TROUBLESHOOT (diagnose 400/404/429/500 eval errors), and STATUS (inspect a live ruleset's version, cache, rate limit, and eval count). Trigger on "where can we use BRMS", "add BRMS / rules to this service", "create a rule for", "evaluate ruleset", or "rule evaluation failing".
license: MIT
x-spec-version: "1.0"
---

# brms-integration

Onboard a service to a BRMS in one guided flow: scan the repo for rule opportunities → build the
ruleset (UI-guided or JDM JSON) → drop in the eval-API client → verify it works. The BRMS is built
on the **GoRules Zen Engine**; rules are authored as **JDM** (JSON Decision Model) graphs of
inputNode → decisionTableNode → outputNode.

> Generic, vendor-neutral. Configure your own base URL and credentials via the documented
> placeholders/env vars — no hardcoded hosts, keys, or tenant ids anywhere.

## When to use
- "Where can we use BRMS in our service?"
- Creating a decision table for fee tiers, eligibility checks, tenure adjustments, or any threshold logic
- Wiring the eval API (`POST /api/v1/evaluate/ruleset/{project_slug}/{ruleset_slug}`) into a service
- An eval call returns an unexpected error (400/404/429/500)
- Checking whether a ruleset is active, cached, or rate-limited

## Modes (auto-detect; can be chained IDENTIFY → BUILD → INTEGRATE)

### Mode 1 — IDENTIFY
Scan the caller's code for hardcoded logic that belongs in BRMS:
- `if`/`elif` chains with numeric thresholds on domain fields (tenure, amount, rate, score)
- nested conditionals driven by domain attributes; dict/list lookups mapping ranges → values (slabs/tiers)
- constants that business teams change every quarter; comments referencing spreadsheets/"business rules"

For each candidate emit: `File:line range`, logic type (decision table | eligibility gate | fee slab |
rate tier), inputs, outputs, a suggested kebab-case ruleset slug, and extraction effort. Confirm which
to target, then go to BUILD.

### Mode 2 — BUILD
Ask: build via **UI** (step-by-step) or **JSON** (generate JDM directly)?
- **UI:** create ruleset (name, kebab-case slug, version `1.0`, status `draft`) → add a Decision Table
  node → set **hit policy** (`first` = first match for priority rules; `collect` = all matches for
  stacking) → add input columns (names must match `input_data` keys exactly) and output columns
  (appear in `result`) → fill rows (`> 9`, `[3,6,9]`, `< 1000`, blank = any) → wire Input → Table →
  Output → Save → **Activate**.
- **JSON:** generate `jdm_content` from `assets/templates/jdm_skeleton.json`, then POST to create
  (draft) and PATCH `{"status":"active"}` to activate. To edit JDM on an active ruleset, include
  `"status":"draft"` in the same PATCH (see pitfalls #2).

### Mode 3 — INTEGRATE
Generate a drop-in eval client for the caller's stack. Templates in `assets/templates/`:
`client_async.py` (httpx, FastAPI/async), `client_sync.py` (requests, Django/Celery),
`client_go.go` (net/http), `client_node.js` (axios). Show how to call `evaluate(input_data)`, read
`result`, and handle `429` (back off) and `400/500`.

### Mode 4 — TROUBLESHOOT
| Symptom | Likely cause | Fix |
|---|---|---|
| `400 "Ruleset is not active"` | ruleset still draft/inactive | PATCH `{"status":"active"}` |
| `400 "Cannot edit … on active ruleset"` | content sent to active ruleset | add `"status":"draft"` to same PATCH |
| `400 "input_data is required"` | missing wrapper | send `{"input_data": {…}}` |
| `404 "Ruleset not found"` | wrong slug/project/version | verify slugs; check default version |
| `429 "Rate limit exceeded"` | over `evaluation_rate_limit_per_sec` | back off 1s / raise limit |
| headers not forwarded | client lowercasing `X-Client-ID`/`X-API-Key` | see pitfalls #1 |

### Mode 5 — STATUS
GET the ruleset and report: status (draft/active/inactive), version + is_default, cache
(enabled/TTL), rate limit (evals/sec), total evaluation count, last evaluated timestamp.

## Files
`assets/templates/` (4 clients + `jdm_skeleton.json`) · `PARAMETERS.md` (all placeholders) ·
`references/{pitfalls.md,decisions.md}`.
