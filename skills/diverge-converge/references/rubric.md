# Gates, thresholds and profiles

**`assets/rubrics.json` is the single source of truth.** This file explains it; if the two
disagree, the JSON wins. After editing the JSON, run
`python3 scripts/test_converge.py` — it asserts the invariants below.

## Gates

A gate is a yes/no question: **"is this rule violated?"** The judge answers with a `noul`
— the probability (0.0-1.0) that it *is* violated.

| gate | violated when |
|---|---|
| `constraint` | it breaks a hard constraint stated in the frame — time window, team size, required tech, budget, an invariant |
| `anti_goal` | its **core mechanism** is one of the listed anti-goals (incidental resemblance does not count) |
| `demo` | no working, demonstrable result is reachable inside the stated window. *No window stated → false.* |
| `checkpoint` | no first decision checkpoint — evidence it works or should stop — is reachable inside the window. *No window stated → false.* |
| `access` | it depends on data, access or partners **this team** cannot realistically obtain |

Gates run at **both** stages. A seed killed at triage never reaches elaboration; a card
killed at score cannot win no matter how it scores.

## Thresholds

| constant | value | meaning |
|---|---|---|
| `KILL` | 0.7 | gate at or above this → **KILLED**, out of the running |
| `PASS` | 0.3 | gate below this → **ok** |
| — | between | **REVIEW** — the agent writes a short reasoning pass in prose |
| `LOW_CONF` | 0.6 | judge confidence below this marks the score `?` |
| `UNSTABLE_NOUL` | 0.3 | gate spread across runs → `~` |
| `UNSTABLE_10` | 2.0 | score spread across runs (1-10 scale) → `~` |
| `TIE` | 0.2 | totals within this are a tie, broken on the profile's tiebreak vector |
| `FLOOR` | 5.5 | a triage diversity slot is reserved only at or above "Plausible" |
| `CLOSE` | 1.5 | a top-two margin below this is a **close call** |

Scores are levels **0-4**, displayed on a 1-10 scale as `1 + 9·level/4`. Fractions are
allowed, so level 2.5 is a legitimate answer.

## Profiles

| profile | evaluator | gates | vectors (weight) | tiebreak |
|---|---|---|---|---|
| **agentic-software** (default) | a senior engineering director evaluating a GitHub submission | constraint, anti_goal, demo, access | signal 0.40, resilience 0.30, buildability 0.30 | buildability |
| **product** | a seed-stage venture partner | constraint, anti_goal, demo, access | pain 0.35, differentiation 0.25, reachability 0.20, validation 0.20 | pain |
| **architecture** | a principal engineer in a design review | constraint, anti_goal, demo, access | simplicity 0.35, isolation 0.25, load 0.20, reversibility 0.20 | simplicity |
| **strategy** | a board member | constraint, anti_goal, **checkpoint**, access | upside 0.30, defensibility 0.25, execution 0.25, reversibility 0.20 | reversibility |

**Strategy uses `checkpoint` instead of `demo`** — a strategic bet rarely produces a
runnable demo in the window, but it must still reach a point where you learn whether to
continue.

### What the vectors mean

- **signal** — engineering depth: explicit state, real orchestration, verification of the
  agent's own output
- **resilience** — unstructured input, bad API responses, timeouts, prompt injection
- **buildability** — can *this* team reach a demonstrable state in *this* window
- **pain / differentiation / reachability / validation** — how acute the problem is, how
  hard to copy, how the first ten users are reached, how cheaply the riskiest assumption
  is tested
- **simplicity / isolation / load / reversibility** — moving parts, blast radius, 10x
  behaviour, cost of backing out
- **upside / defensibility / execution / reversibility** — materiality, moat, capability
  fit, cost of being wrong

## Triage

Triage asks the gates plus one score, `promise`: *how promising is this as an answer to
the frame, weighing depth, robustness and feasibility together?* Levels: **Not worth
pursuing / Weak / Plausible / Strong / Outstanding.**

Ranking:
1. Drop KILLED.
2. **Diversity pass** — reserve a slot for each persona's best seed, but only if it is at
   or above `FLOOR`. Without the floor, a persona that produced nothing good would still
   promote filler.
3. Fill the remaining slots purely by score, up to `shortlist` (default 3).

An item with no persona uses its own id, so persona-less items never share a slot.

## Close calls

When the top-two margin is below `CLOSE`, the script sets `close_call: true` and adds a
`decide` field. **Do not pick for the user.** Name the deciding criterion, state the
trade-off in one sentence, and ask which side they prefer. If they prefer the runner-up,
add a `weights` override reflecting that preference, re-run, and treat that VERDICT as
final.

This rule exists because two judges genuinely disagreed at margins of 0.5 and 1.2 in
testing — see `judging.md`.

## Custom weights

Put a `weights` object in the cards file:

```json
{"profile": "architecture",
 "weights": {"simplicity": 0.5, "isolation": 0.2, "load": 0.15, "reversibility": 0.15}}
```

It must cover **exactly** the profile's vectors, be non-negative, and sum to 1.0 — the
script refuses anything else with a readable message. Use it to record a stated
preference, never to engineer a winner.
