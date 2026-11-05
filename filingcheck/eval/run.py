"""`make eval`: a question file through one mode with the batch runner, then the grader.

Writes `eval/results/<date>_<set>_<mode>.jsonl` (the batch rows, each with its `grade`) and,
next to it, a `.md` file with the one-table summary. Resumable like the batch runner: run the
same command again and only the missing (question, repeat) pairs are asked; every row is
graded again at the end.
"""

import json
from pathlib import Path

from filingcheck.answer.batch import run_batch
from filingcheck.eval.grade import grade, summary_table
from filingcheck.eval.questions import Question
from filingcheck.llm import ChatModel
from filingcheck.retrieval import Retriever
from filingcheck.tools import ToolDeps


def results_path(set_name: str, mode: str, day: str) -> Path:
    """Where one run's rows go, relative to the repository root."""
    return Path("eval") / "results" / f"{day}_{set_name}_{mode}.jsonl"


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
) -> Path:
    """Answer, grade and summarize; return the path of the summary file."""
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
    )
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    graded = [(row, grade(row, by_id[row["id"]])) for row in rows]
    text = "".join(
        json.dumps(row | {"grade": result.model_dump()}) + "\n" for row, result in graded
    )
    partial = out.with_suffix(".jsonl.tmp")
    partial.write_text(text, encoding="utf-8", newline="\n")
    partial.replace(out)
    summary = out.with_suffix(".md")
    title = f"# Evaluation: {questions_path.stem}, {mode}, {repeats} run(s) per question"
    note = (
        "Graded by the deterministic number grader (`filingcheck/eval/grade.py`). Written by "
        f"`make eval`; the rows are in `{out.name}`."
    )
    body = summary_table(graded, mode=mode, settings=settings)
    summary.write_text(f"{title}\n\n{note}\n\n{body}", encoding="utf-8", newline="\n")
    return summary
