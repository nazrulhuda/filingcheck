"""Grade the stored probe rows with the LLM grader, then draw the hand-graded sample.

Run: `uv run python eval/grade_stored.py --key <file outside the repo>` (needs the local database
and OPENROUTER_API_KEY; costs a few cents).

1. The probe rows in `eval/probes/` get LLM grades (`eval/llm_grades/<date>_probes.jsonl`), with
   the questions in `eval/llm_grades/probe_questions.jsonl` (development only) for the text
   probes and each number probe's own gold.
2. A fixed random sample of 40 graded rows is drawn by seed: 15 text answers, 15 number answers
   whose deterministic grade is not `correct`, 10 that are. Sampled rows without an LLM grade (the
   clean ones) are graded too.
3. `eval/llm_grades/<date>_sample_hidden.md` holds each row's question, reference, answer and
   sources with the LLM verdict hidden; the ten rows the owner grades are marked. The verdicts go
   to `--key`, which is kept out of the repo until the hand grades are in.
"""

import argparse
import json
import random
import sys
from datetime import date
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from dotenv import load_dotenv  # noqa: E402

from filingcheck.db import connect  # noqa: E402
from filingcheck.eval.__main__ import sources_reader  # noqa: E402
from filingcheck.eval.grade import grade  # noqa: E402
from filingcheck.eval.llm_grade import (  # noqa: E402
    GRADER_MODEL,
    GradeCache,
    LlmGrade,
    grade_rows,
    llm_grade,
    load_prompt,
    summary,
)
from filingcheck.eval.llm_sample import Candidate, draw_sample, owner_subset  # noqa: E402
from filingcheck.eval.questions import Question  # noqa: E402
from filingcheck.llm.registry import make_chat  # noqa: E402

SEED = 20261112
SIZES = {"text": 15, "number, not clean": 15, "number, clean": 10}
GRADES = REPO / "eval" / "llm_grades"
# Probe labels to the development questions in probe_questions.jsonl.
TEXT_PROBES = {
    "page:C": "probe-001", "ret-008": "probe-001",
    "page:WMT": "probe-002", "ret-024": "probe-002",
    "page:UNH": "probe-003", "ret-040": "probe-003",
    "page:NFLX": "probe-004", "ret-016": "probe-004",
    "page:AXP": "probe-005", "ret-010": "probe-005",
    "fresh:COST": "probe-006", "fresh:PFE": "probe-007", "fresh:JPM": "probe-008",
    "fresh:GOOGL": "probe-009", "fresh:MA": "probe-010", "fresh:GS": "probe-011",
    "fresh:KO": "probe-012", "fresh:NVDA": "probe-013", "fresh:VZ": "probe-014",
    "fresh:NKE": "probe-015",
}  # fmt: skip
# The two Day 26 number examples, with their gold from the facts.
FACT_PROBES = {
    "fact-001": ("COST", 2025, "operating_income", 10383000000, "2024-09-02", "2025-08-31"),
    "fact-002": ("NKE", 2026, "revenue", 46398000000, "2025-06-01", "2026-05-31"),
}


def number_question(
    company: str,
    year: int,
    metric: str,
    gold: int,
    start: str | None = None,
    end: str | None = None,
    text: str = "",
) -> Question:
    """A number question for a probe row, from the row's own company, year, metric and gold."""
    return Question.model_validate({
        "id": "probe-900", "set": "trap", "category": "wrong_fiscal_year",
        "question": text or "?" * 10,
        "company": company, "fiscal_year": year, "metric": metric, "expected_behavior": "answer",
        "gold_value": gold, "gold_unit": "USD", "gold_period_start": start, "gold_period_end": end,
    })  # fmt: skip


def probe_questions(rows: list[dict[str, Any]], by_id: dict[str, Question]) -> dict[str, Question]:
    """Each probe row's question, keyed by the row's id."""
    out: dict[str, Question] = {}
    for row in rows:
        label = row.get("label", "")
        if label in TEXT_PROBES:
            out[row["id"]] = by_id[TEXT_PROBES[label]]
        elif label in FACT_PROBES:
            c, y, m, gold, start, end = FACT_PROBES[label]
            out[row["id"]] = number_question(c, y, m, gold, start, end, row["question"])
        elif row.get("gold") is not None and row.get("company") and row.get("fiscal_year"):
            out[row["id"]] = number_question(
                row["company"],
                row["fiscal_year"],
                row["metric"],
                int(row["gold"]),
                text=row["question"],
            )
    return out


def fact_line(f: dict[str, Any]) -> str:
    """One looked-up fact as the hidden file shows it."""
    period = f.get("instant") or f"{f.get('period_start')} to {f.get('period_end')}"
    return f"{f['concept']} = {f['value']} {f['unit']} ({period})"


def main() -> int:
    """Grade the probe rows, draw the sample, write the hidden file and the key."""
    parser = argparse.ArgumentParser(prog="eval/grade_stored.py")
    parser.add_argument("--key", type=Path, required=True, help="where the hidden verdicts go")
    parser.add_argument("--cap", type=float, default=0.5)
    args = parser.parse_args()
    load_dotenv(REPO / ".env")
    today = date.today().isoformat()
    model = make_chat(GRADER_MODEL, mode="batch")
    cache = GradeCache(GRADES / "cache.jsonl")
    prompt = load_prompt()
    by_id = {
        q.id: q
        for q in (
            Question.model_validate_json(line)
            for line in (GRADES / "probe_questions.jsonl").read_text(encoding="utf-8").splitlines()
            if line
        )
    }
    # Every graded row: (key, row, question, deterministic outcome, LLM grade or None).
    pool: dict[str, tuple[dict[str, Any], Question, str, LlmGrade | None]] = {}
    with connect() as conn:
        sources_for = sources_reader(conn)
        probe_grades: list[tuple[LlmGrade, str, str]] = []
        for path in sorted((REPO / "eval" / "probes").glob("*.jsonl")):
            rows = [
                json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line
            ]
            rows = [r for r in rows if isinstance(r.get("answer"), str) and r["answer"].strip()]
            questions = probe_questions(rows, by_id)
            grades, stopped = grade_rows(
                rows, questions, sources_for=sources_for, model=model, cache=cache, cap_usd=args.cap
            )
            if stopped:
                print(f"STOPPED at the cap in {path.name}")
                return 1
            graded = {(g.id, g.repeat): g for g in grades}
            for row in rows:
                if row["id"] not in questions:
                    continue
                question = questions[row["id"]]
                outcome: str = grade(row, question).outcome
                key = f"eval/probes/{path.name}:{row['id']}:{row.get('repeat', 1)}"
                found = graded.get((row["id"], row.get("repeat", 1)))
                pool[key] = (row, question, outcome, found)
                if found:
                    probe_grades.append((found, outcome, path.name))
        out = GRADES / f"{today}_probes.jsonl"
        out.write_text(
            "".join(json.dumps(g.model_dump() | {"file": f}) + "\n" for g, _, f in probe_grades),
            encoding="utf-8",
            newline="\n",
        )
        out.with_suffix(".md").write_text(
            summary([(g, o) for g, o, _ in probe_grades], title="the stored probe rows"),
            encoding="utf-8",
            newline="\n",
        )
        examples = {
            q.id: q
            for q in (
                Question.model_validate_json(line)
                for line in (REPO / "eval/questions/examples.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line
            )
        }
        for path in sorted((REPO / "eval" / "results").glob("2026-11-*_examples_agent*.jsonl")):
            if path.stem.endswith("_llm"):
                continue
            llm = {}
            llm_path = path.with_name(path.stem + "_llm.jsonl")
            if llm_path.exists():
                for line in llm_path.read_text(encoding="utf-8").splitlines():
                    if line:
                        g = LlmGrade.model_validate_json(line)
                        llm[(g.id, g.repeat)] = g
            for line in path.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                if not isinstance(row.get("answer"), str) or row["id"] not in examples:
                    continue
                question = examples[row["id"]]
                key = f"eval/results/{path.name}:{row['id']}:{row.get('repeat', 1)}"
                pool[key] = (
                    row,
                    question,
                    grade(row, question).outcome,
                    llm.get((row["id"], row.get("repeat", 1))),
                )

        def stratum(question: Question, outcome: str, found: LlmGrade | None) -> str | None:
            if found is not None and found.error:  # a failed grade is never drawn
                found = None
            if question.gold_text or question.category == "unanswerable_text":
                return "text" if found else None
            if question.gold_value is None and question.expected_behavior == "answer":
                return None
            return (
                "number, clean"
                if outcome == "correct"
                else ("number, not clean" if found else None)
            )

        candidates = [
            Candidate(key=k, stratum=s)
            for k, (row, q, o, g) in pool.items()
            if (s := stratum(q, o, g)) is not None
        ]
        sample = draw_sample(candidates, SIZES, seed=SEED)
        owner = set(owner_subset(sample, 10, seed=SEED))
        key_rows = []
        parts = [
            f"# Hand-graded sample for the LLM grader ({today})",
            "",
            f"Drawn by `eval/grade_stored.py` with seed {SEED}: {SIZES['text']} text answers, "
            f"{SIZES['number, not clean']} number answers whose deterministic grade is not "
            f"correct, {SIZES['number, clean']} that are. The LLM verdicts are hidden until the "
            "hand grades are in.",
            "",
            "For each row give a **verdict** (correct, wrong, partly, abstained, asked) and "
            "**supported** (yes, partly, no, n/a), by the rules in `eval/grader_prompt.md`. Rows "
            "marked **[owner]** are the ten the owner also grades, independently. The rows are "
            "shuffled and their strata are not shown, so the order says nothing about any grade.",
            "",
        ]
        shown = list(sample)
        random.Random(SEED + 2).shuffle(shown)  # the strata would hint at the deterministic grade
        for n, candidate in enumerate(shown, 1):
            row, question, outcome, found = pool[candidate.key]
            if found is None:  # a clean row: graded now, for the comparison
                passages, facts = sources_for(row)
                found = llm_grade(
                    question,
                    row,
                    passages=passages,
                    facts=facts,
                    model=model,
                    cache=cache,
                    use="check",
                    prompt=prompt,
                )
                if found.error:
                    print(f"the grade of {candidate.key} failed: {found.error}")
                    return 1
            passages, facts = sources_for(row)
            key_rows.append(
                {
                    "n": n,
                    "key": candidate.key,
                    "stratum": candidate.stratum,
                    "owner": candidate.key in owner,
                    "deterministic": outcome,
                    "verdict": found.verdict,
                    "supported": found.supported,
                    "reason": found.reason,
                }
            )
            mark = " **[owner]**" if candidate.key in owner else ""
            reference = []
            if question.gold_value is not None:
                reference.append(f"Gold value: {question.gold_value} {question.gold_unit}")
            if question.gold_text:
                reference.append(f"Gold text: {question.gold_text}")
            if question.trap_note:
                reference.append(f"Note: {question.trap_note}")
            parts += [
                f"## {n}{mark}",
                "",
                f"Row: `{candidate.key}`",
                "",
                f"**Question:** {row['question']}",
                "",
                f"**Expected behavior:** {question.expected_behavior}; company "
                f"{question.company}, fiscal year {question.fiscal_year}",
                "",
                *[f"- {r}" for r in reference],
                "",
                "**Answer:**",
                "",
                "> " + row["answer"].replace("\n", "\n> "),
                "",
                "**Cited passages:**" if passages else "**Cited passages:** none",
                *[f"\n[{p}] {t}" for p, t in passages],
                "",
                "**Numbers looked up:**" if facts else "**Numbers looked up:** none",
                *[f"- F{i}: {fact_line(f)}" for i, f in enumerate(facts, 1)],
                "",
                "Verdict: ______  Supported: ______",
                "",
            ]
    (GRADES / f"{today}_sample_hidden.md").write_text(
        "\n".join(parts) + "\n", encoding="utf-8", newline="\n"
    )
    args.key.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in key_rows), encoding="utf-8"
    )
    print(f"probe grades: {len(probe_grades)}; sample: {len(sample)} rows")
    print("owner's ten:")
    for key in sorted(owner):
        print(" ", key)
    return 0


if __name__ == "__main__":
    sys.exit(main())
