"""`python -m filingcheck.eval gold` and `python -m filingcheck.eval run` (`make eval`).

gold: fill the gold values of a question file from the facts table (filingcheck/eval/gold.py).
run:  a question set through one mode in batch mode, graded (filingcheck/eval/run.py).
gate-fixture: write the gate's facts fixture from data/facts.jsonl (filingcheck/eval/gate.py).
grade: the LLM grader over a stored results file (filingcheck/eval/llm_grade.py), `make grade`.
dry-run: the Day 33 report over a day's result files, and a hidden sample of text answers
(filingcheck/eval/dryrun.py), `make dry-run`.
"""

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from filingcheck.console import use_utf8_output
from filingcheck.paths import REPO_ROOT

QUESTIONS_DIR = REPO_ROOT / "eval" / "questions"


def gate_fixture_main() -> int:
    """Write tests/eval_gate/facts_fixture.jsonl from data/facts.jsonl."""
    from filingcheck.eval.gate import FIXTURE, load_scenarios, write_fixture
    from filingcheck.paths import DATA_DIR

    facts = DATA_DIR / "facts.jsonl"
    if not facts.exists():
        print("ERROR: no data/facts.jsonl; run make ingest first")
        return 1
    count = write_fixture(load_scenarios(), facts, FIXTURE)
    print(f"wrote {count} rows to {FIXTURE.relative_to(REPO_ROOT)}")
    return 0


def gold_main(args: argparse.Namespace) -> int:
    """Fill the gold values from the facts table, through the agent's own lookup."""
    from filingcheck.db import connect
    from filingcheck.eval.gold import fill_gold_file
    from filingcheck.facts.lookup import PostgresFacts

    with connect() as conn:
        report = fill_gold_file(args.questions, PostgresFacts(conn))
    for qid, action, detail in report:
        print(f"{qid}: {action}" + (f" ({detail})" if detail else ""))
    return 0


def sources_reader(conn: Any) -> Any:
    """Rebuild a stored row's sources for the LLM grader: cited passages' text and its facts."""
    from filingcheck.facts.lookup import PostgresFacts, lookup
    from filingcheck.labels.stored import sources_for_row

    facts_source = PostgresFacts(conn)

    def passage_text(ids: list[int]) -> dict[int, str]:
        rows = conn.execute("SELECT id, text FROM chunks WHERE id = ANY(%s)", (ids,)).fetchall()
        return {int(i): str(t) for i, t in rows}

    def sources_for(row: dict[str, Any]) -> tuple[list[tuple[int, str]], list[dict[str, Any]]]:
        sources, _, _ = sources_for_row(
            row,
            passage_text=passage_text,
            lookup_fact=lambda t, y, metric: lookup(facts_source, t, y, metric),
            filing_facts=None,
        )
        facts = [
            {
                "concept": f.concept,
                "value": str(f.value),
                "unit": f.unit,
                "period_start": f.period_start.isoformat() if f.period_start else None,
                "period_end": f.period_end.isoformat() if f.period_end else None,
                "instant": f.instant.isoformat() if f.instant else None,
            }
            for f in sources.facts
        ]
        return [(p.number, p.text) for p in sources.passages], facts

    return sources_for


def grade_main(args: argparse.Namespace) -> int:
    """Grade a stored results file with the LLM grader; write its grades and a summary page."""
    from filingcheck.db import connect
    from filingcheck.eval.grade import grade
    from filingcheck.eval.llm_grade import GRADER_MODEL, GradeCache, grade_rows, summary
    from filingcheck.eval.run import read_questions
    from filingcheck.llm.registry import make_chat

    questions = {q.id: q for q in read_questions(QUESTIONS_DIR / f"{args.set}.jsonl")}
    rows = [
        json.loads(line)
        for line in args.run.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    model = make_chat(GRADER_MODEL, mode="batch")
    with connect() as conn:
        grades, stopped = grade_rows(
            rows,
            questions,
            sources_for=sources_reader(conn),
            model=model,
            cache=GradeCache(args.cache),
            cap_usd=args.cap,
        )
    outcomes = {
        (r["id"], r.get("repeat", 1)): grade(r, questions[r["id"]]).outcome
        for r in rows
        if r["id"] in questions and isinstance(r.get("answer"), str)
    }
    out = args.run.with_name(args.run.stem + "_llm.jsonl")
    out.write_text(
        "".join(g.model_dump_json() + "\n" for g in grades), encoding="utf-8", newline="\n"
    )
    page = summary([(g, outcomes[(g.id, g.repeat)]) for g in grades], title=args.run.stem)
    out.with_suffix(".md").write_text(page, encoding="utf-8", newline="\n")
    print(page)
    if stopped:
        print(f"STOPPED: the spend passed the cap of ${args.cap}; run again to continue")
        return 1
    return 0


def dryrun_main(args: argparse.Namespace) -> int:
    """Write the dry-run report for one day's result files, and the hidden text sample."""
    import random

    from filingcheck.db import connect
    from filingcheck.eval.dryrun import report
    from filingcheck.eval.grade import grade
    from filingcheck.eval.llm_grade import LlmGrade
    from filingcheck.eval.llm_sample import Candidate, HiddenRow, draw_sample, render_hidden
    from filingcheck.eval.run import read_questions, set_names

    arms: dict[str, dict[str, Any]] = {}
    questions: dict[str, Any] = {}
    pool: dict[str, tuple[dict[str, Any], Any, LlmGrade]] = {}
    for set_name in set_names(args.sets):
        by_id = {q.id: q for q in read_questions(QUESTIONS_DIR / f"{set_name}.jsonl")}
        questions |= by_id
        for arm, label in (("agent-checks-off", "checks off"), ("agent-checks-on", "checks on")):
            path = REPO_ROOT / "eval" / "results" / f"{args.date}_{set_name}_{arm}.jsonl"
            if not path.exists():
                print(f"no {path.relative_to(REPO_ROOT)}: that arm is left out")
                continue
            rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x]
            graded = [(r, grade(r, by_id[r["id"]])) for r in rows if r["id"] in by_id]
            llm: dict[tuple[str, int], LlmGrade] = {}
            llm_path = path.with_name(path.stem + "_llm.jsonl")
            if llm_path.exists():
                for line in llm_path.read_text(encoding="utf-8").splitlines():
                    if line:
                        g = LlmGrade.model_validate_json(line)
                        llm[(g.id, g.repeat)] = g
            else:
                print(f"no {llm_path.relative_to(REPO_ROOT)}: no LLM grades for that arm")
            arms.setdefault(set_name, {})[label] = (graded, llm)
            for row, _ in graded:
                found = llm.get((row["id"], row.get("repeat", 1)))
                if found is not None and found.use == "text" and found.verdict:
                    key = f"eval/results/{path.name}:{row['id']}:{row.get('repeat', 1)}"
                    pool[key] = (row, by_id[row["id"]], found)
    page = REPO_ROOT / "eval" / "results" / f"{args.date}_dry-run.md"
    page.write_text(report(arms, questions, date=args.date), encoding="utf-8", newline="\n")
    print(f"wrote {page.relative_to(REPO_ROOT)}")
    if args.sample_key is None:
        return 0
    candidates = [Candidate(key=k, stratum="text") for k in pool]
    sample = draw_sample(candidates, {"text": args.sample_size}, seed=args.seed)
    random.Random(args.seed + 2).shuffle(sample)
    hidden_rows, key_rows = [], []
    with connect() as conn:
        sources_for = sources_reader(conn)
        for n, candidate in enumerate(sample, 1):
            row, question, g = pool[candidate.key]
            passages, facts = sources_for(row)
            reference = []
            if question.gold_value is not None:
                reference.append(f"Gold value: {question.gold_value} {question.gold_unit}")
            if question.gold_text:
                reference.append(f"Gold text: {question.gold_text}")
            if question.trap_note:
                reference.append(f"Note: {question.trap_note}")
            hidden_rows.append(
                HiddenRow(
                    key=candidate.key,
                    question=row["question"],
                    expected=f"{question.expected_behavior}; company {question.company}, "
                    f"fiscal year {question.fiscal_year}",
                    reference=reference,
                    answer=row["answer"],
                    passages=passages,
                    facts=[_fact_text(f) for f in facts],
                )
            )
            key_rows.append(
                {
                    "n": n,
                    "key": candidate.key,
                    "stratum": "text",
                    "verdict": g.verdict,
                    "supported": g.supported,
                    "reason": g.reason,
                }
            )
    hidden = REPO_ROOT / "eval" / "llm_grades" / f"{args.date}_sample3_hidden.md"
    hidden.write_text(
        render_hidden(
            hidden_rows,
            title=f"Hand-graded sample 3 for the LLM grader ({args.date})",
            intro=f"Drawn by `python -m filingcheck.eval dry-run` with seed {args.seed}: "
            f"{args.sample_size} text answers from the dry run's rows, both arms, with the "
            "LLM verdicts hidden. Give each row a **verdict** (correct, wrong, partly, "
            "abstained, asked) and **supported** (yes, partly, no, n/a), by the rules in "
            "`eval/grader_prompt.md`.",
        ),
        encoding="utf-8",
        newline="\n",
    )
    args.sample_key.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in key_rows), encoding="utf-8"
    )
    print(f"wrote {hidden.relative_to(REPO_ROOT)}; {len(pool)} text rows in the pool")
    return 0


def _fact_text(fact: dict[str, Any]) -> str:
    period = fact.get("instant") or f"{fact.get('period_start')} to {fact.get('period_end')}"
    return f"{fact['concept']} = {fact['value']} {fact['unit']} ({period})"


def run_main(args: argparse.Namespace) -> int:
    """Ask, grade and summarize each named question set in one mode, one after the other."""
    from filingcheck.eval.run import set_names

    for set_name in set_names(args.set):
        code = _run_set(args, set_name)
        if code:
            return code
    return 0


def _run_set(args: argparse.Namespace, set_name: str) -> int:
    """One question set in one mode (batch mode, no fallback); resumable like the batch runner."""
    from filingcheck.answer.batch import BatchFileError
    from filingcheck.answer.run import hybrid_retriever, settings_line
    from filingcheck.checks import reference_data
    from filingcheck.db import connect
    from filingcheck.eval.arms import arm_name
    from filingcheck.eval.run import choose_results_path, read_questions, results_path, run_eval
    from filingcheck.facts.lookup import PostgresFacts
    from filingcheck.llm import router_from_env
    from filingcheck.tools import ToolDeps

    questions = QUESTIONS_DIR / f"{set_name}.jsonl"
    if not questions.exists():
        print(f"ERROR: no question file {questions.relative_to(REPO_ROOT)}")
        return 1
    name = arm_name(args.mode, args.checks)
    if args.date:
        out = REPO_ROOT / results_path(set_name, name, args.date)
    else:
        today = datetime.now(UTC).date().isoformat()
        ids = {q.id for q in read_questions(questions)}
        out = choose_results_path(
            REPO_ROOT,
            set_name,
            name,
            expected_rows=len(ids) * args.repeats,
            today=today,
            question_ids=ids,
        )
        if not out.name.startswith(today):
            print(f"resuming the unfinished {out.relative_to(REPO_ROOT)}")
    out.parent.mkdir(parents=True, exist_ok=True)
    router = router_from_env("batch")
    settings = settings_line(router.primary.name, filters="question text only, no filters")
    print(f"{set_name}: mode batch, {name}; {args.repeats} run(s) per question; {settings}")
    with connect() as conn:
        extra = reference_data() if args.checks else {}
        deps = ToolDeps(retriever=hybrid_retriever(conn), facts=PostgresFacts(conn), **extra)
        try:
            summary = run_eval(
                questions,
                mode=args.mode,
                repeats=args.repeats,
                model=router,
                deps=deps,
                out=out,
                settings=settings,
                checks=args.checks,
            )
        except BatchFileError as exc:
            print(f"ERROR: {exc}")
            return 1
    print(summary.read_text(encoding="utf-8"))
    print(f"wrote {out.relative_to(REPO_ROOT)} and {summary.relative_to(REPO_ROOT)}")
    if args.checks is not None:
        _write_arms(set_name, out, args.checks, questions, args.repeats)
    return 0


def _write_arms(set_name: str, out: Path, checks: bool, questions: Path, repeats: int) -> None:
    """After an agent run: the comparison with the newest finished file of the other arm."""
    from filingcheck.eval.arms import arm_name, arms_path, compare_arms, finished_arm
    from filingcheck.eval.grade import Grade
    from filingcheck.eval.run import read_questions

    ids = {q.id for q in read_questions(questions)}
    other = finished_arm(
        REPO_ROOT,
        set_name,
        arm_name("agent", not checks),
        expected_rows=len(ids) * repeats,
        question_ids=ids,
    )
    if other is None:
        print(f"no finished {arm_name('agent', not checks)} file for {set_name} yet: no comparison")
        return

    def graded(path: Path) -> list[tuple[dict[str, Any], Grade]]:
        rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
        return [(r, Grade.model_validate(r["grade"])) for r in rows if r.get("grade")]

    off, on = (other, out) if checks else (out, other)
    text = compare_arms(
        graded(off), graded(on), set_name=set_name, off_file=off.name, on_file=on.name
    )
    page = REPO_ROOT / arms_path(set_name, out.name[:10])
    page.write_text(text, encoding="utf-8", newline="\n")
    print(text)
    print(f"wrote {page.relative_to(REPO_ROOT)}")


def main(argv: list[str] | None = None) -> int:
    """Parse the command and run it."""
    use_utf8_output()
    parser = argparse.ArgumentParser(prog="python -m filingcheck.eval")
    commands = parser.add_subparsers(dest="command", required=True)
    gold = commands.add_parser("gold", help="fill gold values from the facts table")
    gold.add_argument("--questions", type=Path, default=QUESTIONS_DIR / "examples.jsonl")
    commands.add_parser("gate-fixture", help="write the gate's facts fixture from the facts file")
    run = commands.add_parser("run", help="ask and grade a question set in one mode")
    run.add_argument(
        "--set", required=True, help="question files in eval/questions/, no .jsonl, comma-separated"
    )
    run.add_argument("--mode", choices=["baseline", "agent"], required=True)
    run.add_argument("--repeats", type=int, default=1, help="runs per question (default 1)")
    run.add_argument(
        "--date", help="the results file date (default: an unfinished file's, else today UTC)"
    )
    run.add_argument("--checks", help="agent only: on (default) or off; the file name says which")
    llm = commands.add_parser("grade", help="the LLM grader over a stored results file")
    llm.add_argument("--set", required=True, help="the question file the run answered, no .jsonl")
    llm.add_argument("--run", type=Path, required=True, help="a results file in eval/results/")
    llm.add_argument("--cap", type=float, default=1.0, help="stop once the spend passes this")
    llm.add_argument(
        "--cache", type=Path, default=REPO_ROOT / "eval" / "llm_grades" / "cache.jsonl"
    )
    dry = commands.add_parser("dry-run", help="the Day 33 report and the hidden text sample")
    dry.add_argument("--date", default=datetime.now(UTC).date().isoformat())
    dry.add_argument("--sets", default="dev_traps,dev_unanswerable,control")
    dry.add_argument("--sample-key", type=Path, help="where the hidden sample's verdicts go")
    dry.add_argument("--sample-size", type=int, default=20)
    dry.add_argument("--seed", type=int, default=20261133)
    args = parser.parse_args(argv)
    load_dotenv(REPO_ROOT / ".env")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    if args.command == "gate-fixture":
        return gate_fixture_main()
    if args.command == "gold":
        return gold_main(args)
    if args.command == "grade":
        return grade_main(args)
    if args.command == "dry-run":
        return dryrun_main(args)
    if args.repeats < 1:
        parser.error("--repeats must be 1 or more")
    from filingcheck.eval.arms import checks_argument

    try:
        args.checks = checks_argument(args.mode, args.checks)
    except ValueError as exc:
        parser.error(str(exc))
    return run_main(args)


if __name__ == "__main__":
    sys.exit(main())
