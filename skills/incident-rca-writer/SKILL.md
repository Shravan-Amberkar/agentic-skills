---
name: incident-rca-writer
description: Use when an incident has happened and you need to write a clear, blameless root-cause analysis (RCA) or postmortem from logs, metrics, timelines, and notes. Produces a structured document — summary, impact (who/what/how many/how long), detection, timeline, root cause vs contributing factors, resolution, and concrete preventive action items with owners. Distinguishes trigger from root cause and pushes for systemic fixes (monitoring, guardrails, access control) over one-off patches. Trigger when the user asks to write an RCA/postmortem, analyze an outage or incident, or turn incident notes and logs into a report.
license: MIT
---

# Incident RCA Writer

Turn messy incident notes, logs, and metrics into a crisp, **blameless** root-cause analysis that a
senior engineering org would accept. Focus on systems and process, never individuals.

## When to use
- "Write an RCA / postmortem"
- "Analyze this outage" / "what was the root cause"
- Turning a timeline + logs into a report

## Required structure

1. **Summary** — 2–3 sentences: what broke, when, and the headline impact.
2. **Impact** — quantify: users/records affected, duration (detection→resolution), data integrity,
   money/SLA impact. Be specific (e.g. "4,218 applications affected over 3h12m").
3. **Detection** — how it was found (alert vs customer report) and time-to-detect. If detection was
   slow, that's a finding.
4. **Timeline** — timestamped events from first symptom to full resolution (UTC + local).
5. **Root cause vs contributing factors** — separate the *trigger* (what fired it now) from the
   *root cause* (the underlying condition) and *contributing factors* (what made it worse/slower).
6. **Resolution** — what was done to restore service, and how recovery was verified.
7. **Action items** — each with an owner, a due date, and a type: **Prevent** (stop recurrence),
   **Detect** (catch faster), **Mitigate** (reduce blast radius). Prefer systemic fixes:
   deduplication, idempotency, monitoring/alerts, access control, runbooks, capacity, config guardrails.

## Principles
- **Blameless.** "The deploy step lacked a confirmation guard," not "X deployed the wrong build."
- **Trigger ≠ root cause.** Keep asking "why" until you reach a condition you can systemically fix.
- **Every incident yields at least one Detect and one Prevent action.** A patch alone is not enough.
- **No untracked action items.** Owner + date or it won't happen.

## Output
A clean Markdown document with the sections above. If inputs are thin, list the specific facts still
needed (exact timestamps, affected counts, which alert fired) rather than guessing. Keep it factual
and concise — an RCA is read by people deciding whether to trust the fix.
