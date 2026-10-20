#!/usr/bin/env python3
"""converge.py — build judge requests and tally judge answers for the diverge-converge skill.

The judge (Jev, subagents, or the agent itself) answers a fixed question set.
Every number below is computed here, never by the agent reading a table.

Usage:
    converge.py request CARDS --stage triage|score
    converge.py tally   CARDS --stage triage|score [--judge jev|subagents|self] ANS [ANS2]

Stdlib only. Python 3.8+.
"""

import argparse
import json
import os
import sys

# ---------------------------------------------------------------- constants

# A gate answer is the probability (0..1) that the gate is VIOLATED.
KILL = 0.7   # >= this: the item is out, no further argument
PASS = 0.3   # <  this: the gate is clear
             # between the two: REVIEW — the agent reasons about it in prose

LOW_CONF = 0.6   # judge confidence below this marks the score `?`

# Run-to-run spread across two judge passes. Above these, mark `~` (unstable).
UNSTABLE_NOUL = 0.3   # on the 0..1 gate scale
UNSTABLE_10 = 2.0     # on the 1..10 display scale

# Totals within this are a tie, broken on the profile's tiebreak vector.
# Compare with TIE + 1e-9: in testing, 8.0 - 7.8 came out as 0.20000000000000018.
TIE = 0.2

# A diversity slot in triage is reserved only for seeds at or above "Plausible"
# (level 2 -> 1 + 9*2/4 = 5.5). Below that, one-per-persona would promote filler.
FLOOR = 5.5

# Top-two margin below this is a close call, surfaced to the user rather than
# silently decided. Evidence: agent judges and Jev picked DIFFERENT winners at
# margins of 0.5 and 1.2 in testing; they agreed once the margin exceeded 1.5.
CLOSE = 1.5

JUDGE_LABELS = {
    "jev": "Jev",
    "subagents": "two fresh agent subagents (2 passes)",
    "self": "the authoring agent itself: UNBLINDED, LOW-TRUST, treat scores as indicative",
}

HERE = os.path.dirname(os.path.abspath(__file__))
RUBRICS = os.path.join(HERE, os.pardir, "assets", "rubrics.json")


def die(msg):
    sys.exit("converge.py: " + msg)


def load_json(path, what):
    try:
        with open(path) as fh:
            return json.load(fh)
    except FileNotFoundError:
        die("%s file not found: %s" % (what, path))
    except json.JSONDecodeError as exc:
        die("%s file is not valid JSON (%s): %s" % (what, exc, path))


def load_rubrics():
    return load_json(RUBRICS, "rubrics")


# ---------------------------------------------------------------- validation

def validate_cards(cards, rubrics):
    if not isinstance(cards, dict):
        die("cards file must be a JSON object")

    frame = cards.get("frame")
    if not isinstance(frame, str) or not frame.strip():
        die("cards.frame must be a non-empty string — the judge scores against it")

    profile_name = cards.get("profile", "agentic-software")
    profiles = rubrics["profiles"]
    if profile_name not in profiles:
        die("unknown profile %r. Valid profiles: %s"
            % (profile_name, ", ".join(sorted(profiles))))
    profile = profiles[profile_name]

    items = cards.get("items")
    if not isinstance(items, dict) or not items:
        die("cards.items must be a non-empty object of id -> {persona, text}")

    for item_id, item in items.items():
        if "__" in item_id:
            die("item id %r contains '__', which separates item from question id. "
                "Rename it." % item_id)
        if not isinstance(item, dict):
            die("item %r must be an object with a 'text' field" % item_id)
        if not isinstance(item.get("text"), str) or not item["text"].strip():
            die("item %r has no non-empty 'text'" % item_id)

    weights = cards.get("weights")
    if weights is not None:
        vectors = set(profile["vectors"])
        if not isinstance(weights, dict):
            die("cards.weights must be an object of vector -> weight")
        given = set(weights)
        if given != vectors:
            missing = sorted(vectors - given)
            extra = sorted(given - vectors)
            parts = []
            if missing:
                parts.append("missing " + ", ".join(missing))
            if extra:
                parts.append("unknown " + ", ".join(extra))
            die("cards.weights must cover exactly the %s vectors (%s): %s"
                % (profile_name, ", ".join(sorted(vectors)), "; ".join(parts)))
        for key, val in weights.items():
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                die("weight for %r must be a number" % key)
            if val < 0:
                die("weight for %r is negative (%s); weights must be >= 0" % (key, val))
        total = sum(weights.values())
        if abs(total - 1.0) > 1e-6:
            die("cards.weights must sum to 1.0, got %.4f" % total)

    shortlist = cards.get("shortlist", 3)
    if not isinstance(shortlist, int) or isinstance(shortlist, bool) or shortlist < 1:
        die("cards.shortlist must be a positive integer")

    anti_goals = cards.get("anti_goals", [])
    if not isinstance(anti_goals, list):
        die("cards.anti_goals must be a list of strings")

    return profile_name, profile


def weights_for(cards, profile):
    override = cards.get("weights")
    if override:
        return dict(override)
    return {k: v["weight"] for k, v in profile["vectors"].items()}


# ---------------------------------------------------------------- request

def build_request(cards, rubrics, stage):
    profile_name, profile = validate_cards(cards, rubrics)
    gates = profile["gates"]
    evaluator = profile["evaluator"]

    state = {
        "frame": cards["frame"],
        "anti_goals": cards.get("anti_goals", []),
    }
    questions = {}

    for item_id, item in cards["items"].items():
        ref = "`item_%s`" % item_id
        state["item_%s" % item_id] = item["text"]

        for gate in gates:
            spec = rubrics["gates"][gate]
            questions["%s__%s" % (item_id, gate)] = {
                "type": "noul",
                "instructions": spec["instructions"].replace("{item}", ref),
                "criteria": spec["criteria"],
            }

        if stage == "triage":
            spec = rubrics["triage"]
            questions["%s__promise" % item_id] = {
                "type": "score",
                "instructions": (spec["instructions"]
                                 .replace("{item}", ref)
                                 .replace("{evaluator}", evaluator)),
                "criteria": spec["criteria"],
            }
        else:
            for vec, spec in profile["vectors"].items():
                questions["%s__%s" % (item_id, vec)] = {
                    "type": "score",
                    "instructions": (spec["instructions"]
                                     .replace("{item}", ref)
                                     .replace("{evaluator}", evaluator)),
                    "criteria": spec["criteria"],
                }

    return {"state": state, "questions": questions}


# ---------------------------------------------------------------- answers

def validate_answers(answers, request, path):
    if not isinstance(answers, dict):
        die("answers file %s must be a JSON object of question id -> answer" % path)

    questions = request["questions"]
    for qid, spec in questions.items():
        if qid not in answers:
            die("answers file %s is missing question %r" % (path, qid))
        ans = answers[qid]
        if not isinstance(ans, dict):
            die("answer for %r must be an object like {\"noul\": 0.2} or {\"score\": 2.5}" % qid)

        kind = spec["type"]
        if kind not in ans:
            other = "score" if kind == "noul" else "noul"
            hint = ""
            if other in ans:
                hint = (" — this is a %s question, so it needs \"%s\", not \"%s\""
                        % (kind, kind, other))
            die("answer for %r has no %r key%s" % (qid, kind, hint))

        val = ans[kind]
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            die("answer for %r: %r must be a number, got %r" % (qid, kind, val))

        if kind == "noul":
            if not 0.0 <= val <= 1.0:
                die("answer for %r: noul is %s, but it must be a probability in 0..1 "
                    "— a probability, not a percent" % (qid, val))
        else:
            top = len(spec["criteria"]) - 1
            if not 0.0 <= val <= top:
                die("answer for %r: score is %s, but it must be a level in 0..%d "
                    "— levels, not a 1-10 score" % (qid, val, top))

        if "confidence" in ans:
            conf = ans["confidence"]
            if isinstance(conf, bool) or not isinstance(conf, (int, float)):
                die("answer for %r: confidence must be a number" % qid)
            if not 0.0 <= conf <= 1.0:
                die("answer for %r: confidence is %s, but it must be in 0..1" % (qid, conf))


def merge(runs, request):
    """Mean across runs, min confidence, max-min spread."""
    merged = {}
    for qid, spec in request["questions"].items():
        kind = spec["type"]
        vals = [r[qid][kind] for r in runs]
        confs = [r[qid].get("confidence") for r in runs]
        confs = [c for c in confs if c is not None]
        merged[qid] = {
            "value": sum(vals) / len(vals),
            "confidence": min(confs) if confs else None,
            "spread": max(vals) - min(vals) if len(vals) > 1 else 0.0,
            "levels": len(spec["criteria"]) if kind == "score" else None,
        }
    return merged


def to_ten(level):
    """Map a 0..4 level onto the 1..10 display scale."""
    return round(1 + 9 * level / 4, 1)


# ---------------------------------------------------------------- scoring

def gate_status(value):
    if value >= KILL:
        return "KILLED"
    if value < PASS:
        return "ok"
    return "REVIEW"


def build_rows(cards, request, merged, profile, stage, weights):
    gates = profile["gates"]
    vectors = ["promise"] if stage == "triage" else list(profile["vectors"])
    rows = []

    for item_id, item in cards["items"].items():
        failed, review, shaky = [], [], []
        for gate in gates:
            m = merged["%s__%s" % (item_id, gate)]
            st = gate_status(m["value"])
            if st == "KILLED":
                failed.append(gate)
            elif st == "REVIEW":
                review.append(gate)
            if m["spread"] >= UNSTABLE_NOUL:
                shaky.append(gate)

        scores, marks = {}, {}
        for vec in vectors:
            m = merged["%s__%s" % (item_id, vec)]
            ten = to_ten(m["value"])
            scores[vec] = ten
            mark = ""
            if m["confidence"] is not None and m["confidence"] < LOW_CONF:
                mark += "?"
            if to_ten(m["value"] + m["spread"]) - ten >= UNSTABLE_10 or \
               (m["spread"] > 0 and 9 * m["spread"] / 4 >= UNSTABLE_10):
                mark += "~"
            marks[vec] = mark

        if stage == "triage":
            total = scores["promise"]
        else:
            total = round(sum(scores[v] * weights[v] for v in vectors), 1)

        status = "KILLED" if failed else ("REVIEW" if review else "ok")
        rows.append({
            "id": item_id,
            "persona": item.get("persona") or item_id,
            "status": status,
            "failed": failed,
            "review": review,
            "shaky": shaky,
            "scores": scores,
            "marks": marks,
            "total": total,
        })
    return rows, vectors


# ---------------------------------------------------------------- verdicts

def triage_verdict(rows, shortlist_n):
    alive = [r for r in rows if r["status"] != "KILLED"]
    alive.sort(key=lambda r: (-r["total"], r["id"]))

    chosen, seen = [], set()
    # First pass: reserve one slot for each persona's best seed, but only if that
    # seed is at least "Plausible". Without FLOOR, a weak persona promotes filler.
    for row in alive:
        if row["persona"] in seen:
            continue
        if row["total"] >= FLOOR and len(chosen) < shortlist_n:
            chosen.append(row)
            seen.add(row["persona"])

    # Then fill remaining slots purely by score.
    for row in alive:
        if len(chosen) >= shortlist_n:
            break
        if row not in chosen:
            chosen.append(row)

    chosen.sort(key=lambda r: (-r["total"], r["id"]))
    verdict = {"shortlist": [r["id"] for r in chosen]}
    needs_review = [r["id"] for r in chosen if r["status"] == "REVIEW"]
    if needs_review:
        verdict["review"] = needs_review
    return verdict


def score_verdict(rows, profile, weights):
    alive = [r for r in rows if r["status"] != "KILLED"]
    if not alive:
        return {"winner": None,
                "reason": "every item was killed by a gate; revisit the frame or the seeds"}

    by_total = sorted(alive, key=lambda r: (-r["total"], r["id"]))
    top = by_total[0]["total"]
    tied = [r for r in by_total if top - r["total"] <= TIE + 1e-9]

    tiebreak = profile["tiebreak"]
    winner = tied[0]
    tiebroken = False
    if len(tied) > 1:
        winner = max(tied, key=lambda r: (r["scores"].get(tiebreak, 0), -1))
        tiebroken = winner["id"] != by_total[0]["id"] or True

    runner_up = None
    for row in by_total:
        if row["id"] != winner["id"]:
            runner_up = row
            break

    # margin is computed on the total ordering, independent of the tie-break,
    # so it can never come out negative.
    margin = round(by_total[0]["total"] - by_total[1]["total"], 1) if len(by_total) > 1 else None

    verdict = {"winner": winner["id"]}
    if runner_up:
        verdict["runner_up"] = runner_up["id"]
    if margin is not None:
        verdict["margin"] = margin
        verdict["close_call"] = margin < CLOSE
        if verdict["close_call"]:
            verdict["decide"] = (
                "ask the user; to prefer %s, re-run with a weights override and take "
                "that VERDICT as final" % (runner_up["id"] if runner_up else "the runner-up"))
    if len(tied) > 1 and tiebroken:
        verdict["tiebreak"] = ("totals within %.1f; broken on %s" % (TIE, tiebreak))
    if winner["review"]:
        verdict["review"] = ("winner has an uncertain gate: %s — reason about it before "
                             "the blueprint" % ", ".join(winner["review"]))
    return verdict


# ---------------------------------------------------------------- render

def render(rows, vectors, verdict, judge, stage):
    out = []
    if judge:
        out.append("Judge: %s" % JUDGE_LABELS.get(judge, judge))
        out.append("")

    head = ["item", "persona", "status", "gates"] + vectors + ["total"]
    out.append("| " + " | ".join(head) + " |")
    out.append("|" + "|".join(["---"] * len(head)) + "|")

    ordered = sorted(rows, key=lambda r: (r["status"] == "KILLED", -r["total"], r["id"]))
    for row in ordered:
        gate_note = ""
        if row["failed"]:
            gate_note = "✗ " + ", ".join(row["failed"])
        elif row["review"]:
            gate_note = "? " + ", ".join(row["review"])
        if row["shaky"]:
            gate_note += (" ~" + ",".join(row["shaky"])) if gate_note else ("~" + ",".join(row["shaky"]))
        cells = [row["id"], row["persona"], row["status"], gate_note or "-"]
        for vec in vectors:
            cells.append("%s%s" % (row["scores"][vec], row["marks"][vec]))
        cells.append(str(row["total"]))
        out.append("| " + " | ".join(cells) + " |")

    out.append("")
    out.append("Legend: gate >= %.1f KILLED, < %.1f ok, between REVIEW · `?` judge "
               "confidence < %.1f · `~` run-to-run spread · scores mapped to 1-10."
               % (KILL, PASS, LOW_CONF))
    out.append("")
    out.append("VERDICT " + json.dumps(verdict, sort_keys=True))
    return "\n".join(out)


# ---------------------------------------------------------------- commands

def cmd_request(args):
    rubrics = load_rubrics()
    cards = load_json(args.cards, "cards")
    print(json.dumps(build_request(cards, rubrics, args.stage), indent=2))


def cmd_tally(args):
    rubrics = load_rubrics()
    cards = load_json(args.cards, "cards")
    profile_name, profile = validate_cards(cards, rubrics)
    request = build_request(cards, rubrics, args.stage)

    runs = []
    for path in args.answers:
        ans = load_json(path, "answers")
        validate_answers(ans, request, path)
        runs.append(ans)

    merged = merge(runs, request)
    weights = weights_for(cards, profile)
    rows, vectors = build_rows(cards, request, merged, profile, args.stage, weights)

    if args.stage == "triage":
        verdict = triage_verdict(rows, cards.get("shortlist", 3))
    else:
        verdict = score_verdict(rows, profile, weights)

    print(render(rows, vectors, verdict, args.judge, args.stage))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    req = sub.add_parser("request", help="build the judge request JSON")
    req.add_argument("cards")
    req.add_argument("--stage", choices=["triage", "score"], required=True)
    req.set_defaults(func=cmd_request)

    tal = sub.add_parser("tally", help="tally judge answers into a table and VERDICT")
    tal.add_argument("cards")
    tal.add_argument("--stage", choices=["triage", "score"], required=True)
    tal.add_argument("--judge", choices=["jev", "subagents", "self"], default=None)
    tal.add_argument("answers", nargs="+")
    tal.set_defaults(func=cmd_tally)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
