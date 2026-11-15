"""The page's results strip: web/data/results.json, written by `make report` from the same
comparisons as the report's headline and S1, formatted as the report formats them."""

from dataclasses import replace

from filingcheck.eval.final_render import HELD, OFF, ON, RULES, _acc, _cw, results_summary
from filingcheck.eval.final_report import claims_reduction, compare
from tests.eval.test_final_charts import final


def test_the_results_file_holds_the_headline_and_the_prompt_rules_comparison() -> None:
    f = final()
    # The prompt-rules arm costs more per question, as in the final run.
    f.scores = [replace(s, cost_usd=0.0005) if s.arm == RULES else s for s in f.scores]
    r = results_summary(f)

    held = compare(f.part(HELD, OFF), f.part(HELD, ON), _cw, majority=True)
    acc = compare(f.part(HELD, RULES), f.part(HELD, ON), _acc, majority=True)
    cw = compare(f.part(HELD, RULES), f.part(HELD, ON), _cw, majority=True)

    assert r["report"] == "eval/results/2026-11-14_final_report.md"
    assert r["tag"] == "week6-measured"
    assert r["held_out"] == {"questions": 16, "runs": 3}
    assert r["headline"] == {
        "checks_off": f"{100 * held.first:.1f}%",
        "checks_on": f"{100 * held.second:.1f}%",
        "difference": f"{100 * held.interval.estimate:+.1f}",
        "low": f"{100 * held.interval.low:+.1f}",
        "high": f"{100 * held.interval.high:+.1f}",
        "claimed": claims_reduction(held),
    }
    p = r["prompt_rules"]
    assert (p["accuracy"], p["accuracy_checks"]) == (
        f"{100 * acc.first:.1f}%",
        f"{100 * acc.second:.1f}%",
    )
    assert (p["accuracy_difference"], p["accuracy_low"], p["accuracy_high"]) == (
        f"{100 * acc.interval.estimate:+.1f}",
        f"{100 * acc.interval.low:+.1f}",
        f"{100 * acc.interval.high:+.1f}",
    )
    assert (p["confidently_wrong"], p["confidently_wrong_checks"]) == (
        f"{100 * cw.first:.1f}%",
        f"{100 * cw.second:.1f}%",
    )
    # Clear means the interval of the difference leaves out zero.
    assert p["accuracy_clear"] == (acc.interval.high < 0 or acc.interval.low > 0)
    assert p["confidently_wrong_clear"] == (cw.interval.high < 0 or cw.interval.low > 0)
    # Cost per 100 questions as the ablation table shows it, and the ratio to one decimal.
    assert (p["cost_per_100"], p["cost_per_100_checks"]) == ("$0.1500", "$0.0900")
    assert p["cost_ratio"] == "1.7"
