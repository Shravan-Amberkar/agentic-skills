---
name: diverge-converge
description: "Multi-perspective brainstorming and evaluation built on Guilford's divergent-to-convergent cycle: isolated personas generate seeds with judgment switched off, per-rule kill gates and a promise score cut them to a shortlist, shortlisted cards are elaborated and pre-mortemed, then a weighted rubric picks exactly ONE winner and writes a blueprint for it. Judging is done by TypeSafe Jev when installed, otherwise by fresh agent subagents; a shipped stdlib Python script does ALL arithmetic — scale mapping, weights, kill thresholds, tie-breaks, shortlisting and close-call detection — so the agent never recomputes numbers by hand. Profiles: agentic-software (default), product, architecture, strategy. Use when asked 'give me project ideas for X', 'brainstorm and pick the best', 'what should I build for Y', 'evaluate these options', or when a vague goal has to become one committed plan. Not for implementing an already-chosen design."
x-spec-version: 1.0
---

# diverge-converge

J.P. Guilford's insight: **divergent** thinking expands possibilities with judgment
switched off; **convergent** thinking criticises, scores and commits. LLM brainstorms
usually fail by blending the two — ideas arrive pre-filtered into the obvious, and
"evaluation" politely crowns whatever was written last.

This skill keeps the phases hard-separated and runs the rhythm **twice**:

```
FRAME ─► DIVERGE ──────► CUT ─────────► ELABORATE ────────► CONVERGE ─────────► BLUEPRINT
         seeds: fluency, gates +        full cards +        gates + rubric,     spec for the
         flexibility,    promise →      pre-mortem patch    reasons, steelman,  ONE winner
         originality     shortlist      (elaboration)       ONE winner
         (no judging)    (converge)     (diverge)           (converge)
```

**Judge vs. arithmetic.** Every *judgment* — did this break a hard rule, how good is it
on criterion X — comes from a JUDGE answering a fixed question set. Every *number* —
scale mapping, weights, kill thresholds, tie-breaks, shortlisting, close-call detection
— comes from `scripts/converge.py`. The judge is Jev when installed, otherwise fresh
agent subagents. Same questions, same answer shape, same scorecard either way.
**Never recompute a number by hand, and never hand-edit a score.**

## When to use

- Ideation: "give me project ideas for X", "what should I build for Y"
- Choosing between approaches: "which of these designs should we pick?"
- Turning a vague goal into a committed plan

"**Evaluate these options**" skips DIVERGE: put the user's options straight into the
cards file as items and start at CONVERGE.

## Instructions

### 0. FRAME — never skip

- Collect three inputs: **Target** (audience, company or goal), **Focus** (domain),
  **Constraint tier** (time, team, tech, budget, invariants). If any is missing, ask
  once with `AskUserQuestion` — one question per missing input, 2-4 concrete options.
- Pick a **profile** and **persona set**; state both in one line so the user can override.
- Write the frame as **one paragraph with every hard constraint explicit** — the gates
  are judged against it, so a constraint left out is a constraint not enforced. List the
  **anti-goals** too.
- **Detect the judge once:** `command -v jev` → `jev`; else the Agent tool is available →
  `subagents`; else `self`. Say which you are using and pass it to every tally as
  `--judge`.
- If Jev: tell the user cards are sent to TypeSafe for scoring. Keep customer data and
  secrets out of the frame.
- Work files go in `mktemp -d`.

### 1. DIVERGE — seeds, judgment banned

- **Isolate the personas.** One FRESH subagent per persona, all launched in a single
  message so they run in parallel. **Never `fork`** — a fork inherits this conversation
  and the voices collapse into one. Each subagent sees only the frame, the anti-goals,
  and its own persona card. Without subagents, write each persona's block fully before
  starting the next and never reference an earlier block.
- **Fluency:** 2 seeds per persona (~6 total). A seed is a **name plus a two-sentence
  mechanism** — nothing longer at this stage.
- **Flexibility:** a persona's two seeds must use different core mechanisms.
- **Originality:** at least one seed must break an assumption in the frame — an
  assumption, never a hard constraint.
- **No evaluation words.** "Feasible", "risky", "simple" and their cousins belong to the
  convergent phases.
- De-duplicate seeds sharing a core mechanism. A merged seed **keeps the persona of the
  higher-ranked original**; it must not become a new combined persona, or it would take
  two diversity slots in triage.

### 2. CUT — first convergence

- Run a triage round (`--stage triage`); show the table.
- One line per dropped seed with the reason.
- For each id in the VERDICT's `review` list, write a short reasoning pass on the
  uncertain gate. If it clearly fails, drop it and promote the next seed.

### 3. ELABORATE — second divergence

- Expand each shortlisted seed into a full concept card **in its author persona's voice**
  (card shape per profile: `references/blueprint.md`).
- **Pre-mortem:** the persona most opposed to the card names the single most likely
  production failure.
- The author patches once (≤2 sentences) or states "accepted risk".
- Write `shortlist.json`.

### 4. CONVERGE — one winner

- Score in the profile's evaluator voice.
- Run a score round (`--stage score`); show the table. KILLED items are out. Any REVIEW
  gate, or any `?` / `~` mark, gets a short reasoning pass saying whether it could change
  the winner.
- **One sentence of reasoning per score** — the judge supplies numbers, you supply reasons.
- **Steelman the runner-up** in two sentences. If that exposes a scoring error, fix the
  frame or the card and re-run. Never hand-edit numbers.
- If the VERDICT has `close_call: true`: say so, name the deciding criterion, and **ask
  the user which side of the trade-off they prefer BEFORE the blueprint**. If they prefer
  the runner-up, add a `weights` override reflecting that, re-run, and treat that VERDICT
  as final.
- **Exactly ONE winner.** Never "combine all of them".
- **Steal list:** ≤2 elements from losing cards, each with a reason.

### 5. BLUEPRINT

Write the profile's sections from `references/blueprint.md`.

- For **agentic-software**, code must be syntactically valid, tools typed, and no `...`
  left in control flow.
- Verify library APIs against current docs (Context7 or WebFetch), or say inline that you
  could not.
- End with **"Risks & first 3 build steps"**.

### 6. Iterate

Offer once — "re-run with other personas, a harder constraint, a deeper blueprint, or
score your own idea" — and never re-run unprompted.

## Where this sits next to the planning pipeline

This skill answers **"which idea?"**. `plan-feature-e2e`, `grill-my-plan`, `plan-to-spec`,
`spec-tech-suggestions`, `spec-to-ticket` and `spec-to-docs` answer **"is this one idea
solid, and how do we ship it?"**.

The hand-off is **optional**. Only when the winner is a feature in an existing repo AND
those skills are installed, ask once before the blueprint: "Full blueprint here (default)"
/ "Short blueprint + `plan-feature-e2e`" / "Short blueprint + `grill-my-plan` only".
Never shorten the blueprint without that answer. For greenfield or non-repo work, write
the full blueprint and don't ask.

## Output contract

Headings, in order: **Frame · Diverge · Cut · Elaborate · Converge · Blueprint · Risks &
first steps.**

Inline by default. If the user asks for a file, write
`docs/ideation/<yyyy-mm-dd>-<slug>.md` with the cards and answer files beside it.

## References

- `references/judging.md` — running a round with Jev or with agent judges; the verbatim judge prompt
- `references/personas.md` — persona sets per profile, and the anti-goal lists
- `references/rubric.md` — gates, thresholds, profiles, close calls, custom weights
- `references/blueprint.md` — seed format, concept cards and blueprint sections per profile
- `assets/rubrics.json` — single source of truth for gates, triage, profiles and weights
- `scripts/converge.py` — builds judge requests, tallies answers, does all arithmetic
- `scripts/test_converge.py` — self-check; run it after touching the script or the rubrics
