#!/usr/bin/env python3
"""Self-check for converge.py. Plain asserts; run as a script."""

import io
import json
import os
import sys
import tempfile
import contextlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import converge as C  # noqa: E402

RUBRICS = C.load_rubrics()


# ---------------------------------------------------------------- helpers

def level_for(ten):
    """Inverse of to_ten: the 0..4 level that displays as `ten` on the 1..10 scale."""
    return (ten - 1) * 4.0 / 9.0


def cards(items, profile="agentic-software", frame="Build a thing in 3 weeks, 1 engineer.",
          **extra):
    out = {"profile": profile, "frame": frame, "anti_goals": ["a chat wrapper"],
           "items": items}
    out.update(extra)
    return out


def answers_for(request, gate=0.1, scores=None, conf=None):
    """Build a complete answer set; `scores` maps 'item__vector' -> 1..10 display value."""
    scores = scores or {}
    out = {}
    for qid, spec in request["questions"].items():
        if spec["type"] == "noul":
            val = gate.get(qid, 0.1) if isinstance(gate, dict) else gate
            out[qid] = {"noul": val}
        else:
            ten = scores.get(qid, 5.5)
            ans = {"score": level_for(ten)}
            if conf is not None:
                ans["confidence"] = conf.get(qid, 1.0) if isinstance(conf, dict) else conf
            out[qid] = ans
    return out


def tally(card, stage, *answer_sets, judge=None):
    request = C.build_request(card, RUBRICS, stage)
    profile = RUBRICS["profiles"][card.get("profile", "agentic-software")]
    for ans in answer_sets:
        C.validate_answers(ans, request, "<memory>")
    merged = C.merge(list(answer_sets), request)
    weights = C.weights_for(card, profile)
    rows, vectors = C.build_rows(card, request, merged, profile, stage, weights)
    if stage == "triage":
        verdict = C.triage_verdict(rows, card.get("shortlist", 3))
    else:
        verdict = C.score_verdict(rows, profile, weights)
    text = C.render(rows, vectors, verdict, judge, stage)
    return rows, verdict, text


def expect_exit(fn, needle):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stderr(buf):
            fn()
    except SystemExit as exc:
        msg = str(exc) or buf.getvalue()
        assert needle.lower() in msg.lower(), \
            "expected %r in exit message, got: %s" % (needle, msg)
        return
    raise AssertionError("expected SystemExit mentioning %r" % needle)


# ---------------------------------------------------------------- tests

def test_request_shape():
    card = cards({"A": {"persona": "Visionary", "text": "an idea"},
                  "B": {"persona": "Cynic", "text": "another idea"}})
    profile = RUBRICS["profiles"]["agentic-software"]

    req = C.build_request(card, RUBRICS, "score")
    expected = 2 * (len(profile["gates"]) + len(profile["vectors"]))
    assert len(req["questions"]) == expected, len(req["questions"])

    tri = C.build_request(card, RUBRICS, "triage")
    assert len(tri["questions"]) == 2 * (len(profile["gates"]) + 1)

    assert req["state"]["item_A"] == "an idea"
    text = req["questions"]["A__signal"]["instructions"]
    assert "`item_A`" in text, text
    assert "{item}" not in text and "{evaluator}" not in text


def test_score_statuses_and_winner_skips_killed():
    card = cards({
        "A": {"persona": "P1", "text": "killed"},
        "B": {"persona": "P2", "text": "under review"},
        "C": {"persona": "P3", "text": "clean and best"},
    })
    req = C.build_request(card, RUBRICS, "score")
    gates = {}
    for qid, spec in req["questions"].items():
        if spec["type"] != "noul":
            continue
        gates[qid] = 0.1
    gates["A__demo"] = 0.9      # >= KILL
    gates["B__access"] = 0.5    # between PASS and KILL
    scores = {}
    for qid, spec in req["questions"].items():
        if spec["type"] == "score":
            scores[qid] = 9.0 if qid.startswith("A__") else 7.0
    rows, verdict, _ = tally(card, "score", answers_for(req, gate=gates, scores=scores))

    by_id = {r["id"]: r for r in rows}
    assert by_id["A"]["status"] == "KILLED"
    assert by_id["B"]["status"] == "REVIEW"
    assert by_id["C"]["status"] == "ok"
    assert verdict["winner"] != "A", "a killed item must never win despite top scores"


def test_not_close_margin():
    card = cards({"A": {"persona": "P1", "text": "strong"},
                  "B": {"persona": "P2", "text": "weaker"}})
    req = C.build_request(card, RUBRICS, "score")
    scores = {}
    for qid, spec in req["questions"].items():
        if spec["type"] == "score":
            scores[qid] = 8.0 if qid.startswith("A__") else 6.4
    _, verdict, _ = tally(card, "score", answers_for(req, scores=scores))
    assert verdict["winner"] == "A"
    assert verdict["margin"] == 1.6, verdict
    assert verdict["close_call"] is False, verdict
    assert "decide" not in verdict


def test_tiebreak_and_close_call():
    # C totals 8.0 flat; B totals 7.8 but is top on buildability (the tiebreak).
    card = cards({"B": {"persona": "P1", "text": "buildable"},
                  "C": {"persona": "P2", "text": "flat"}})
    req = C.build_request(card, RUBRICS, "score")
    scores = {
        "B__signal": 6.8, "B__resilience": 7.0, "B__buildability": 10.0,
        "C__signal": 8.0, "C__resilience": 8.0, "C__buildability": 8.0,
    }
    rows, verdict, _ = tally(card, "score", answers_for(req, scores=scores))
    by_id = {r["id"]: r for r in rows}
    assert by_id["C"]["total"] == 8.0, by_id["C"]["total"]
    assert by_id["B"]["total"] == 7.8, by_id["B"]["total"]
    assert verdict["winner"] == "B", verdict
    assert verdict["margin"] == 0.2 and verdict["margin"] >= 0
    assert verdict["close_call"] is True
    assert "decide" in verdict
    assert "tiebreak" in verdict and "buildability" in verdict["tiebreak"]


def test_stability_mark_and_mean():
    card = cards({"A": {"persona": "P1", "text": "disputed"}})
    req = C.build_request(card, RUBRICS, "score")
    low = answers_for(req, scores={q: 1.0 for q in req["questions"]})
    high = answers_for(req, scores={q: 10.0 for q in req["questions"]})
    rows, _, _ = tally(card, "score", low, high)
    row = rows[0]
    assert row["scores"]["signal"] == 5.5, row["scores"]
    assert "~" in row["marks"]["signal"], row["marks"]


def test_low_confidence_mark():
    card = cards({"A": {"persona": "P1", "text": "uncertain"}})
    req = C.build_request(card, RUBRICS, "score")
    ans = answers_for(req, conf=0.4)
    rows, _, _ = tally(card, "score", ans)
    assert "?" in rows[0]["marks"]["signal"]


def test_triage_diversity_and_floor():
    # Diversity: P2's weaker seed beats P1's second seed for the reserved slot.
    card = cards({"A": {"persona": "P1", "text": "best"},
                  "B": {"persona": "P1", "text": "second"},
                  "C": {"persona": "P2", "text": "other voice"}},
                 shortlist=2)
    req = C.build_request(card, RUBRICS, "triage")
    scores = {"A__promise": 8.0, "B__promise": 7.0, "C__promise": 6.0}
    _, verdict, _ = tally(card, "triage", answers_for(req, scores=scores))
    assert verdict["shortlist"] == ["A", "C"], verdict

    # FLOOR: P2's only seed sits below "Plausible", so it gets no reserved slot.
    low = cards({"A": {"persona": "P1", "text": "best"},
                 "B": {"persona": "P1", "text": "second"},
                 "C": {"persona": "P2", "text": "weak voice"}},
                shortlist=2)
    req2 = C.build_request(low, RUBRICS, "triage")
    scores2 = {"A__promise": 8.0, "B__promise": 7.0, "C__promise": 3.2}
    _, verdict2, _ = tally(low, "triage", answers_for(req2, scores=scores2))
    assert verdict2["shortlist"] == ["A", "B"], verdict2


def test_triage_review_listed():
    card = cards({"A": {"persona": "P1", "text": "uncertain gate"}}, shortlist=1)
    req = C.build_request(card, RUBRICS, "triage")
    gates = {q: 0.1 for q, s in req["questions"].items() if s["type"] == "noul"}
    gates["A__access"] = 0.5
    _, verdict, _ = tally(card, "triage", answers_for(req, gate=gates,
                                                      scores={"A__promise": 8.0}))
    assert verdict["shortlist"] == ["A"]
    assert verdict.get("review") == ["A"], verdict


def test_personaless_items_get_own_slot():
    card = cards({"A": {"text": "one"}, "B": {"text": "two"}}, shortlist=2)
    req = C.build_request(card, RUBRICS, "triage")
    rows, verdict, _ = tally(card, "triage",
                             answers_for(req, scores={"A__promise": 8.0,
                                                      "B__promise": 7.0}))
    personas = {r["persona"] for r in rows}
    assert personas == {"A", "B"}, personas
    assert verdict["shortlist"] == ["A", "B"]


def test_strategy_uses_checkpoint_not_demo():
    card = cards({"A": {"persona": "P1", "text": "a bet"}}, profile="strategy")
    req = C.build_request(card, RUBRICS, "strategy" and "score")
    ids = set(req["questions"])
    assert "A__checkpoint" in ids
    assert "A__demo" not in ids
    assert "A__reversibility" in ids


def test_all_killed_gives_null_winner():
    card = cards({"A": {"persona": "P1", "text": "doomed"}})
    req = C.build_request(card, RUBRICS, "score")
    gates = {q: 0.95 for q, s in req["questions"].items() if s["type"] == "noul"}
    _, verdict, _ = tally(card, "score", answers_for(req, gate=gates))
    assert verdict["winner"] is None
    assert "reason" in verdict


def test_validation_errors():
    good = {"A": {"persona": "P1", "text": "x"}}
    expect_exit(lambda: C.validate_cards(cards(good, profile="nope"), RUBRICS),
                "unknown profile")
    expect_exit(lambda: C.validate_cards(cards({}), RUBRICS), "non-empty object")
    expect_exit(lambda: C.validate_cards(cards({"A__B": {"text": "x"}}), RUBRICS), "__")
    expect_exit(lambda: C.validate_cards(cards(good, frame="  "), RUBRICS), "frame")
    expect_exit(lambda: C.validate_cards(cards({"A": {"persona": "P", "text": ""}}), RUBRICS),
                "text")
    expect_exit(lambda: C.validate_cards(
        cards(good, weights={"signal": 0.5, "resilience": 0.2, "buildability": 0.2}), RUBRICS),
        "sum to 1.0")
    expect_exit(lambda: C.validate_cards(
        cards(good, weights={"signal": 1.2, "resilience": -0.1, "buildability": -0.1}), RUBRICS),
        "negative")
    expect_exit(lambda: C.validate_cards(
        cards(good, weights={"signal": 0.5, "resilience": 0.5}), RUBRICS),
        "missing")


def test_bad_answers():
    card = cards({"A": {"persona": "P1", "text": "x"}})
    req = C.build_request(card, RUBRICS, "score")
    base = answers_for(req)

    def mutate(qid, value):
        bad = dict(base)
        bad[qid] = value
        return lambda: C.validate_answers(bad, req, "<memory>")

    expect_exit(mutate("A__signal", {"score": 7}), "levels, not a 1-10 score")
    expect_exit(mutate("A__constraint", {"noul": 20}), "probability, not a percent")
    expect_exit(mutate("A__constraint", {"score": 0.1}), "noul")
    expect_exit(mutate("A__signal", {"score": 2, "confidence": 2}), "confidence")
    expect_exit(mutate("A__signal", {"score": True}), "must be a number")

    missing = dict(base)
    del missing["A__signal"]
    expect_exit(lambda: C.validate_answers(missing, req, "<memory>"), "missing question")


def test_rubrics_invariants():
    gates = set(RUBRICS["gates"])
    assert len(RUBRICS["triage"]["criteria"]) == 5
    for name, profile in RUBRICS["profiles"].items():
        total = sum(v["weight"] for v in profile["vectors"].values())
        assert abs(total - 1.0) < 1e-9, "%s weights sum to %s" % (name, total)
        assert profile["tiebreak"] in profile["vectors"], name
        assert set(profile["gates"]) <= gates, name
        for vname, vec in profile["vectors"].items():
            assert len(vec["criteria"]) == 5, "%s.%s" % (name, vname)
            assert "{item}" in vec["instructions"], "%s.%s" % (name, vname)


def test_render_self_judge_warns():
    card = cards({"A": {"persona": "P1", "text": "x"}})
    req = C.build_request(card, RUBRICS, "score")
    _, _, text = tally(card, "score", answers_for(req), judge="self")
    assert "LOW-TRUST" in text, text
    assert "VERDICT " in text
    assert text.splitlines()[0].startswith("Judge:")


def test_cli_round_trip():
    card = cards({"A": {"persona": "P1", "text": "x"}, "B": {"persona": "P2", "text": "y"}})
    with tempfile.TemporaryDirectory() as tmp:
        cpath = os.path.join(tmp, "cards.json")
        apath = os.path.join(tmp, "ans.json")
        with open(cpath, "w") as fh:
            json.dump(card, fh)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            C.main(["request", cpath, "--stage", "score"])
        req = json.loads(buf.getvalue())
        with open(apath, "w") as fh:
            json.dump(answers_for(req), fh)
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            C.main(["tally", cpath, "--stage", "score", "--judge", "jev", apath])
        out = buf2.getvalue()
        assert "VERDICT " in out and "Judge: Jev" in out


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print("ok %s" % name)
        except AssertionError as exc:
            failures += 1
            print("FAIL %s: %s" % (name, exc))
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print("ERROR %s: %s: %s" % (name, type(exc).__name__, exc))
    print()
    print("%d failed" % failures if failures else "all tests passed")
    sys.exit(1 if failures else 0)
