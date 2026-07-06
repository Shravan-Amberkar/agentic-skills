# Architecture Decisions

Why the BRMS is designed this way — the interview-worthy reasoning.

### Why externalize business rules at all
Threshold logic (fee slabs, tenure adjustments, eligibility) changes on a business cadence, not an
engineering one. Hardcoding it means a deploy for every tweak and risky `if/elif` sprawl.
Externalizing to versioned decision tables lets business/ops change rules without a release, with an
audit trail of what changed and when.

### Why GoRules Zen Engine + JDM
Zen Engine evaluates JDM (JSON Decision Model) graphs fast and embeddably. JDM is a portable,
inspectable representation (inputNode → decisionTableNode → outputNode) that both a visual editor and
an API can produce — so rules authored in the UI and rules generated as JSON are the same artifact.

### Why multi-tenant with X-Client-ID + X-API-Key
One BRMS serves many services/teams. `X-Client-ID` scopes the tenant; `X-API-Key` authenticates the
caller. This isolates rulesets per tenant and lets a key be revoked without affecting others.

### Why ruleset versioning + draft/active status
A ruleset has versions and a status. Callers evaluate the active/default version; editors iterate on a
draft without breaking production traffic. `1.x` versions allow non-breaking iteration; activation is
an explicit, auditable step.

### Why per-ruleset caching + rate limits
Hot rulesets with stable inputs benefit from short-TTL caching (huge eval-count reduction). Per-ruleset
rate limits protect the engine from a runaway caller and make capacity predictable.

### Why a hit policy (first vs collect)
`first` returns the first matching row — natural for priority-ordered rules (return the first tier that
matches). `collect` returns all matches — needed when effects stack (e.g. multiple surcharges apply).
Choosing the wrong policy is a common modeling bug.
