# diverge-converge

A multi-perspective brainstorming and evaluation engine built on J.P. Guilford's
divergent-to-convergent thinking cycle.

## Why

LLM brainstorms fail in two specific ways, and they are the same failure at opposite ends:

1. **Judgment leaks into ideation.** Ask for ten ideas and you get ten sensible, obvious
   ones, because the model filters as it generates. The interesting idea was pre-rejected
   before it was written down.
2. **Evaluation is theatre.** Ask the same model to pick the best and it crowns whatever
   it wrote last, with a paragraph of agreeable reasoning attached.

This skill fixes both by **hard-separating the phases** and by **taking the arithmetic
away from the agent entirely**.

## The flow

```
FRAME ─► DIVERGE ──────► CUT ─────────► ELABORATE ────────► CONVERGE ─────────► BLUEPRINT
         seeds: fluency, gates +        full cards +        gates + rubric,     spec for the
         flexibility,    promise →      pre-mortem patch    reasons, steelman,  ONE winner
         originality     shortlist      (elaboration)       ONE winner
         (no judging)    (converge)     (diverge)           (converge)
```

| Step | Mode | Guilford factor | What happens |
|---|---|---|---|
| FRAME | — | — | Target, focus, constraints; profile and personas picked; judge detected |
| DIVERGE | divergent | fluency, flexibility, originality | Isolated personas write 2 seeds each; no evaluation words allowed |
| CUT | **convergent** | — | Kill gates + a promise score cut to a shortlist |
| ELABORATE | divergent | elaboration | Full cards, then a pre-mortem from the most hostile persona |
| CONVERGE | **convergent** | — | Gates + weighted rubric; steelman the runner-up; exactly ONE winner |
| BLUEPRINT | — | — | The winner's spec, plus risks and the first three build steps |

## Judge vs. arithmetic

Every **judgment** comes from a judge answering a fixed question set. Every **number** —
scale mapping, weights, kill thresholds, tie-breaks, shortlisting, close-call detection —
comes from `scripts/converge.py`, a stdlib-only Python script.

The agent never recomputes a number and never hand-edits a score. If a score looks wrong,
you fix the frame or the card and re-run.

## Profiles

| profile | evaluator | vectors (weight) | tiebreak |
|---|---|---|---|
| **agentic-software** (default) | senior engineering director reviewing a GitHub submission | signal 0.40, resilience 0.30, buildability 0.30 | buildability |
| **product** | seed-stage venture partner | pain 0.35, differentiation 0.25, reachability 0.20, validation 0.20 | pain |
| **architecture** | principal engineer in a design review | simplicity 0.35, isolation 0.25, load 0.20, reversibility 0.20 | simplicity |
| **strategy** | board member | upside 0.30, defensibility 0.25, execution 0.25, reversibility 0.20 | reversibility |

All four run the gates `constraint`, `anti_goal` and `access`. The first three add `demo`
(is a working result reachable?); strategy swaps in `checkpoint` (is a decision point
reachable?).

## With or without Jev

| | Jev | Agent subagents | Self |
|---|---|---|---|
| Independence | external judge | two fresh subagents | none — unblinded |
| Runs needed | 1 (effectively deterministic) | 2 | 2, low trust |
| Catches | noise **and** model bias | noise only — same model, same biases | little |
| Cost | a TypeSafe API call | two subagent runs | free |
| Data | cards sent to TypeSafe | stays local | stays local |

**An honest note:** in testing, an uncalibrated agent judge scored a poll-everything
design 8.3/10 on load where Jev gave 3.0. The calibrated judge prompt closed most of that
gap — but the two judges still picked **different winners** on a close call. That is why
margins under 1.5 are surfaced to you as a close call rather than decided silently.

## Install

```sh
npx skills add Shravan-Amberkar/agentic-skills --skill diverge-converge
```

Optional, for the stronger judge: install TypeSafe's `jev` CLI so it is on `PATH`, with the key in
`TYPESAFE_API_KEY` or `~/.config/typesafe/env`. Without it the skill falls back to agent judges.

Requires `python3` (3.8+). No other dependencies.

## Example prompts

- "Give me project ideas for a payments company hiring AI engineers"
- "Brainstorm approaches to our webhook reliability problem and pick the best one"
- "What should I build to demonstrate agentic engineering in three weeks?"
- "**Score my 3 ideas**" — skips DIVERGE; your options go straight into the cards file and
  the run starts at CONVERGE
- "Use the architecture profile: should we shard, add read replicas, or cache?"

## Where it fits

This skill answers **"which idea?"**. The planning pipeline — `plan-feature-e2e`,
`grill-my-plan`, `plan-to-spec`, `spec-tech-suggestions`, `spec-to-ticket`,
`spec-to-docs` — answers **"is this one idea solid, and how do we ship it?"**.

The hand-off is optional and only offered when the winner is a feature in an existing repo
and those skills are installed.

## Layout

```
diverge-converge/
├── SKILL.md                    agent-facing instructions
├── README.md                   this file
├── assets/rubrics.json         single source of truth: gates, triage, profiles, weights
├── scripts/converge.py         stdlib-only: builds judge requests, tallies answers
├── scripts/test_converge.py    self-check — run after touching the script or rubrics
└── references/
    ├── personas.md             persona sets per profile + anti-goals
    ├── rubric.md               gates, thresholds, profiles, close calls, custom weights
    ├── blueprint.md            seed format, card shapes, blueprint sections
    └── judging.md              running a round with Jev or agent judges
```
