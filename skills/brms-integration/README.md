# brms-integration (Agent Skill)

Adopt a **BRMS (Business Rules Management System)** built on the **GoRules Zen Engine** — move
hardcoded `if/elif` thresholds, fee slabs, and rate tiers into versioned, externally-managed decision
tables. Vendor-neutral and environment-driven; works with any BRMS that exposes the documented API.

## Install
```bash
npx skills add Shravan-Amberkar/brms-integration
# or copy this directory into your agent's skills folder
```

## The 5 modes
| Mode | Say something like | What you get |
|---|---|---|
| **IDENTIFY** | "where can we use BRMS here?" | a report of rule candidates with file:line, inputs/outputs, effort |
| **BUILD** | "create a rule for tenure adjustment" | guided UI steps **or** generated JDM JSON + create/activate curls |
| **INTEGRATE** | "add the eval client to this service" | a typed client (async-py / sync-py / Go / Node) + usage |
| **TROUBLESHOOT** | "rule evaluation is failing" | cause + fix from the error table |
| **STATUS** | "is this ruleset active?" | version, status, cache, rate limit, eval count |

## What you need before starting
| Thing | Where to get it |
|---|---|
| Base URL | your BRMS deployment (env var `BRMS_BASE_URL`) |
| Project slug | BRMS UI → Projects |
| Tenant Client ID (`X-Client-ID`) | your BRMS admin |
| API Key (`X-API-Key`) | your BRMS admin |

## Evaluation API (quick reference)
```bash
curl -X POST '$BRMS_BASE_URL/api/v1/evaluate/ruleset/<project_slug>/<ruleset_slug>' \
  -H 'Content-Type: application/json' \
  -H 'X-Client-ID: <tenant_client_id>' \
  -H 'X-API-Key: <api_key>' \
  -d '{"input_data": {"tenure_months": 12, "loan_amount": 50000}}'
# -> { "result": { "effect_type": "PCT_ADD", "effect_value": 2 } }
```

## JDM model (how a rule is shaped)
```
inputNode  --edge-->  decisionTableNode  --edge-->  outputNode
(schema)              (inputs, outputs, rules, hitPolicy)     (result)
```
Hit policy: `first` (first matching row — priority rules) or `collect` (all matches — stacking).

## Top pitfalls
1. **Editing an active ruleset** → include `"status":"draft"` in the same PATCH.
2. **`input_data is required`** → wrap fields under `input_data`.
3. **Headers dropped** → keep `X-Client-ID` / `X-API-Key` case intact.

See [`references/pitfalls.md`](references/pitfalls.md), [`references/decisions.md`](references/decisions.md),
and [`PARAMETERS.md`](PARAMETERS.md). Templates (4 clients + JDM skeleton) live in `assets/templates/`.

## License
MIT © Shravan Amberkar
