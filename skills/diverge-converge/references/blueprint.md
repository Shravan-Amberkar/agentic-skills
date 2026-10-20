# Seeds, concept cards and blueprints

Three artefacts, three stages. Keeping them distinct is what stops DIVERGE from
collapsing into premature design.

| stage | artefact | size |
|---|---|---|
| DIVERGE | **seed** | a name + two sentences of mechanism |
| ELABORATE | **concept card** | the profile's card shape, written in the author persona's voice |
| BLUEPRINT | **blueprint** | the profile's sections, for the ONE winner |

**Seeds stay short on purpose.** A long seed smuggles evaluation into the divergent
phase, and it biases triage toward whoever wrote the most. Full cards are written only
after the cut.

## The cards file

```json
{
  "profile": "agentic-software",
  "frame": "One paragraph with every hard constraint explicit.",
  "anti_goals": ["a search or chat wrapper", "standard RAG over a doc folder"],
  "shortlist": 3,
  "items": {
    "A": {"persona": "Blue-sky Product Visionary", "text": "<seed, then the full card>"},
    "B": {"persona": "Cynical Tech Stack Lead", "text": "..."}
  }
}
```

`shortlist` and `weights` are optional. Item ids must not contain `__`. The same file is
used at both stages — at ELABORATE you replace each shortlisted seed's `text` with its
full card and drop the rest.

## Pre-mortem (ELABORATE)

For each shortlisted card: **the persona most opposed to it** names the single most
likely production failure — one specific failure, not a list of risks. The author then
patches the card once in **≤2 sentences**, or writes **"accepted risk"** and says why.

A pre-mortem that produces no change is a pre-mortem that was not taken seriously; so is
one that rewrites the card.

---

## agentic-software

**Concept card**
- **Architectural Identity** — what kind of system this is, in one line
- **Agentic State Loop** — the states, the transitions, and the typed payload carried
  between them
- **Differentiator** — what this does that the anti-goals cannot

**Blueprint**
1. **Topology + why** — the components and why this shape rather than the obvious one
2. **State machine** — a text diagram including **retry, escalate and terminal** edges,
   not just the happy path
3. **Tool matrix** — at least 3 tools: name · typed inputs · logic · typed return ·
   failure handled
4. **Production stack** — the fewest libraries that work, with one line of *why* each
5. **Bootstrap file** — a single runnable Python file: typed state, tools, nodes, routing,
   a **hard iteration cap**, and a working `__main__`

Code must be syntactically valid with no `...` left in control flow. Verify library APIs
against current docs, or say inline that you could not.

---

## product

**Concept card**
- **Name**
- **Target user and the painful moment** — who, and the specific moment it hurts
- **Core mechanic** — what the product actually does
- **Why now** — what changed that makes this possible or necessary today

**Blueprint**
1. **ICP and job-to-be-done**
2. **MVP: in and out** — the out-list matters more than the in-list
3. **Riskiest assumption and the cheapest test** — the test must be cheaper than building
4. **Metrics** — the one number that says it is working, plus its guardrail
5. **30-day plan**

---

## architecture

**Concept card**
- **Name**
- **Shape** — the structure in one line
- **Key bet** — the assumption the design rests on
- **Makes easy / makes hard** — both halves, honestly

**Blueprint**
1. **Component diagram** (text)
2. **Data and control flow** — including what happens on the write path under contention
3. **Failure modes and isolation** — per component: what fails, who notices, what degrades
4. **Capacity estimate** — show the arithmetic
5. **Migration path** — from what exists today, in steps that are each individually safe
6. **ADR** — context, decision, consequences, and what would make us revisit it

---

## strategy

**Concept card**
- **Name**
- **Thesis** — the claim about the world
- **Mechanism of advantage** — why this compounds rather than decays
- **Signal it is working** — observable, and early

**Blueprint**
1. **Thesis and assumptions** — each assumption separately falsifiable
2. **Milestones with kill criteria** — a milestone without a kill criterion is a wish
3. **Resource ask** — people, money, time, and what gets starved to fund it
4. **Competitor responses** — the two most likely, and the answer to each
5. **Review date** — when this gets re-examined regardless of how it is going
