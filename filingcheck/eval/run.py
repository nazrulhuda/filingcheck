"""`make eval`: a question file through one mode with the batch runner, then the grader.

Writes `eval/results/<date>_<set>_<mode>.jsonl` (the batch rows, each with its `grade`) and,
next to it, a `.md` file with the one-table summary. Resumable like the batch runner: run the
same command again and only the missing (question, repeat) pairs are asked; every row is
graded again at the end. Without a date, an unfinished file of the same set and mode is
resumed. A row whose question is no longer in the question file is kept but not graded.
"""

import json
from pathlib import Path

from filingcheck.answer.batch import run_batch
from filingcheck.eval.grade import grade, summary_table
from filingcheck.eval.questions import Question
from filingcheck.llm import ChatModel
from filingcheck.retrieval import Retriever
from filingcheck.tools import ToolDeps

DATED = "[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]"


def results_path(set_name: str, mode: str, day: str) -> Path:
    """Where one run's rows go, relative to the repository root."""
    return Path("eval") / "results" / f"{day}_{set_name}_{mode}.jsonl"


def choose_results_path(
    root: Path,
    set_name: str,
    mode: str,
    *,
    expected_rows: int,
    today: str,
    question_ids: set[str] | None = None,
) -> Path:
    """Today's results file, unless the newest earlier file of this set and mode is unfinished.

    A run resumed after midnight UTC then goes on in its own file instead of starting again.
    With `question_ids`, only rows of current questions count toward `expected_rows`.
    """
    todays = root / results_path(set_name, mode, today)
    if todays.exists():
        return todays
    earlier = sorted((root / "eval" / "results").glob(f"{DATED}_{set_name}_{mode}.jsonl"))
    if earlier:
        newest = earlier[-1]
        rows = [
            json.loads(line)
            for line in newest.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if question_ids is not None:
            rows = [r for r in rows if r.get("id") in question_ids]
        if len(rows) < expected_rows:
            return newest
    return todays


def read_questions(path: Path) -> list[Question]:
    """The questions of one file, in file order."""
    return [
        Question.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def run_eval(
    questions_path: Path,
    *,
    mode: str,
    repeats: int,
    model: ChatModel,
    deps: ToolDeps,
    out: Path,
    settings: str,
    retriever: Retriever | None = None,
    checks: bool | None = None,
) -> Path:
    """Answer, grade and summarize; return the path of the summary file.

    `checks` is the agent's switch (None for the baseline); the title names the arm.
    """
    questions = read_questions(questions_path)
    by_id = {q.id: q for q in questions}
    run_batch(
        [(q.id, q.question) for q in questions],
        mode=mode,
        out=out,
        model=model,
        deps=deps,
        settings=settings,
        retriever=retriever,
        repeats=repeats,
        checks=bool(checks),
    )
    rows = [
        json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    grades = {i: grade(row, by_id[row["id"]]) for i, row in enumerate(rows) if row["id"] in by_id}
    graded = [(rows[i], result) for i, result in grades.items()]
    stale = len(rows) - len(graded)
    text = "".join(
        json.dumps(row | {"grade": grades[i].model_dump() if i in grades else None}) + "\n"
        for i, row in enumerate(rows)
    )
    partial = out.with_suffix(".jsonl.tmp")
    partial.write_text(text, encoding="utf-8", newline="\n")
    partial.replace(out)
    summary = out.with_suffix(".md")
    runs = max((row.get("repeat", 1) for row, _ in graded), default=0)
    arm = mode if checks is None else f"{mode}, checks {'on' if checks else 'off'}"
    title = f"# Evaluation: {questions_path.stem}, {arm}, {runs} run(s) per question"
    note = (
        "Graded by the deterministic number grader (`filingcheck/eval/grade.py`). Written by "
        f"`make eval`; the rows are in `{out.name}`."
    )
    if stale:
        rows_word, verb = ("row", "is") if stale == 1 else ("rows", "are")
        note += (
            f" {stale} {rows_word} whose question is no longer in `{questions_path.name}` "
            f"{verb} kept in the file and not graded."
        )
    body = summary_table(graded, mode=arm, settings=settings)
    summary.write_text(f"{title}\n\n{note}\n\n{body}", encoding="utf-8", newline="\n")
    return summary
