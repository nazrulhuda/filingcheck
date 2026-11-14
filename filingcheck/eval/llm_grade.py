"""The LLM grader: a second model reads a stored answer and its sources and gives a verdict.

Uses (Week 5): the main grade for text questions (`gold_text`, `unanswerable_text`); a second
opinion on every number question whose deterministic grade is not `correct`, which stays the
main grade for numbers; and `supported` on every text answer, which measures answers that are
confidently unsupported by their own sources.

The prompt is `eval/grader_prompt.md`; its version is its first line plus a hash of the file,
so a changed prompt never reuses old results. Each result is cached by a hash of the model, the
prompt version and the messages, in a JSONL file, so the same inputs are graded and paid for
once. No temperature is sent: the grader model on OpenRouter does not accept one, and the
cache keeps a run repeatable.
"""

import hashlib
import json
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from filingcheck.eval.grade import Grade, grade
from filingcheck.eval.questions import Question
from filingcheck.llm import ChatModel, Message, ProviderError
from filingcheck.paths import REPO_ROOT

PROMPT_FILE = REPO_ROOT / "eval" / "grader_prompt.md"
# A different model family from the one being graded (decisions, 2026-11-12).
GRADER_MODEL = "openrouter:anthropic/claude-haiku-5.5"
MAX_TOKENS = 1500  # at 600, 3 of 99 text grades ran out (reasoning counts toward it)
Verdict = Literal["correct", "wrong", "partly", "abstained", "asked"]
Supported = Literal["yes", "partly", "no", "n/a"]
Passages = list[tuple[int, str]]
Facts = list[dict[str, Any]]


class LlmVerdict(BaseModel):
    """What the grader model must return."""

    model_config = ConfigDict(extra="forbid")

    verdict: Verdict
    supported: Supported
    reason: str
    evidence: str


VERDICT_SCHEMA: dict[str, Any] = {
    "name": "grade",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["verdict", "supported", "reason", "evidence"],
        "properties": {
            "verdict": {"type": "string", "enum": list(Verdict.__args__)},  # type: ignore[attr-defined]
            "supported": {"type": "string", "enum": list(Supported.__args__)},  # type: ignore[attr-defined]
            "reason": {"type": "string"},
            "evidence": {"type": "string"},
        },
    },
}


class LlmGrade(BaseModel):
    """One answer's LLM grade, with what produced it."""

    id: str
    repeat: int
    use: str  # "text" or "second opinion"
    verdict: Verdict | None
    supported: Supported | None
    reason: str
    evidence: str
    model: str
    prompt_version: str
    cost_usd: float | None
    cached: bool
    error: str | None = None


def load_prompt(path: Path = PROMPT_FILE) -> tuple[str, str]:
    """The prompt text and its version: the number on its first line and a hash of the file."""
    text = path.read_text(encoding="utf-8")
    number = text.splitlines()[0].removeprefix("Version:").strip()
    return text, f"{number}-{hashlib.sha256(text.encode()).hexdigest()[:12]}"


def needs_llm(
    question: Question, deterministic: Grade, *, every_number: bool = False
) -> str | None:
    """Why the LLM grader reads this row: "text", "also accept", "second opinion", or None.

    The second opinion goes to number-graded runs the deterministic grader failed; with
    `every_number` (the Week 6 final run) to every number-graded run, passed or failed, so a
    wrong answer the deterministic grader passed is checked too. It never changes a grade.
    """
    if question.gold_text or question.category == "unanswerable_text":
        return "text"
    if deterministic.llm_decides:  # the question's also_accept note: the LLM grader decides
        return "also accept"
    if every_number or deterministic.outcome != "correct":
        return "second opinion"
    return None


def _reference(question: Question) -> list[str]:
    lines = [f"Expected behavior: {question.expected_behavior}"]
    if question.gold_value is not None:
        period = (
            f"as of {question.gold_instant}"
            if question.gold_instant
            else f"{question.gold_period_start} to {question.gold_period_end}"
            if question.gold_period_start
            else "the fiscal year asked about"
        )
        lines.append(f"Gold value: {question.gold_value} {question.gold_unit} ({period})")
    if question.company or question.fiscal_year:
        lines.append(f"Company and fiscal year meant: {question.company}, {question.fiscal_year}")
    if question.gold_text:
        lines.append(f"Gold text: {question.gold_text}")
    if question.trap_note:
        lines.append(f"Note: {question.trap_note}")
    also = question.also_accept
    if also is not None:
        if also.expected_behavior:
            lines.append(f"Also accept: expected behavior {also.expected_behavior}")
        if also.gold_value is not None:
            value = f"{also.gold_value} {also.gold_unit}"
            lines.append(f"Also accept: {value} for fiscal year {also.fiscal_year}")
        if also.note:
            lines.append(f"Also accept: {also.note}")
    return lines


def _fact_line(n: int, fact: Mapping[str, Any]) -> str:
    period = (
        f"as of {fact['instant']}"
        if fact.get("instant")
        else f"{fact.get('period_start')} to {fact.get('period_end')}"
    )
    return f"F{n}: {fact['concept']} = {fact['value']} {fact['unit']}, {period}"


def build_messages(
    question: Question, answer: str, *, passages: Passages, facts: Facts, prompt: str
) -> list[Message]:
    """The system prompt, then the question, the reference, the answer and its sources."""
    parts = [f"Question: {question.question}", *_reference(question), "", f"Answer:\n{answer}", ""]
    parts.append("Cited passages:" if passages else "Cited passages: none")
    parts += [f"[{n}] {text}" for n, text in passages]
    parts.append("Numbers looked up:" if facts else "Numbers looked up: none")
    parts += [_fact_line(n, fact) for n, fact in enumerate(facts, 1)]
    return [{"role": "system", "content": prompt}, {"role": "user", "content": "\n".join(parts)}]


class GradeCache:
    """LLM grades by input hash, in a JSONL file that only grows."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.records: dict[str, dict[str, Any]] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    record = json.loads(line)
                    self.records[record["input_sha256"]] = record

    def get(self, key: str) -> dict[str, Any] | None:
        """The cached grade for these inputs, if there is one."""
        return self.records.get(key)

    def put(self, key: str, record: dict[str, Any]) -> None:
        """Keep a grade and append it to the file."""
        self.records[key] = {"input_sha256": key, **record}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(self.records[key], ensure_ascii=False) + "\n")


def _key(model: str, version: str, messages: list[Message]) -> str:
    body = json.dumps({"model": model, "prompt": version, "messages": messages}, sort_keys=True)
    return hashlib.sha256(body.encode()).hexdigest()


def llm_grade(
    question: Question,
    row: Mapping[str, Any],
    *,
    passages: Passages,
    facts: Facts,
    model: ChatModel,
    cache: GradeCache,
    use: str = "text",
    prompt: tuple[str, str] | None = None,
) -> LlmGrade:
    """The LLM grade of one stored answer, from the cache when the inputs were graded before."""
    text, version = prompt or load_prompt()
    messages = build_messages(question, row["answer"], passages=passages, facts=facts, prompt=text)
    key = _key(model.name, version, messages)
    base = {"id": row["id"], "repeat": row.get("repeat", 1), "use": use, "model": model.name}
    cached = cache.get(key)
    if cached is not None:
        return LlmGrade(
            **base,
            verdict=cached["verdict"],
            supported=cached["supported"],
            reason=cached["reason"],
            evidence=cached["evidence"],
            prompt_version=version,
            cost_usd=0.0,
            cached=True,
            error=cached.get("error"),
        )
    completion = model.complete(messages, max_tokens=MAX_TOKENS, json_schema=VERDICT_SCHEMA)
    try:
        verdict: LlmVerdict | None = LlmVerdict.model_validate_json(completion.text)
        error = None
    except ValidationError:
        verdict, error = None, "invalid verdict"
    result = LlmGrade(
        **base,
        verdict=verdict.verdict if verdict else None,
        supported=verdict.supported if verdict else None,
        reason=verdict.reason if verdict else completion.text[:300],
        evidence=verdict.evidence if verdict else "",
        prompt_version=version,
        cost_usd=completion.cost_usd,
        cached=False,
        error=error,
    )
    cache.put(
        key,
        result.model_dump(
            include={"id", "repeat", "verdict", "supported", "reason", "evidence", "error"}
        )
        | {"cost_usd": completion.cost_usd, "prompt_version": version},
    )
    return result


def grade_rows(
    rows: Iterable[Mapping[str, Any]],
    questions: Mapping[str, Question],
    *,
    sources_for: Callable[[Mapping[str, Any]], tuple[Passages, Facts]],
    model: ChatModel,
    cache: GradeCache,
    cap_usd: float,
    every_number: bool = False,
) -> tuple[list[LlmGrade], bool]:
    """LLM grades for the rows that need one; stops once the spend passes `cap_usd`.

    Returns the grades and whether the cap stopped the run. `every_number` gives every
    number-graded run a second opinion (see `needs_llm`).
    """
    prompt = load_prompt()
    grades: list[LlmGrade] = []
    spent = 0.0
    for row in rows:
        question = questions.get(row["id"])
        if question is None or not isinstance(row.get("answer"), str):
            continue
        use = needs_llm(question, grade(dict(row), question), every_number=every_number)
        if use is None:
            continue
        passages, facts = sources_for(row)
        try:
            result = llm_grade(
                question,
                row,
                passages=passages,
                facts=facts,
                model=model,
                cache=cache,
                use=use,
                prompt=prompt,
            )
        except ProviderError as exc:
            result = LlmGrade(
                id=row["id"],
                repeat=row.get("repeat", 1),
                use=use,
                verdict=None,
                supported=None,
                reason="",
                evidence="",
                model=model.name,
                prompt_version=prompt[1],
                cost_usd=None,
                cached=False,
                error=exc.log_code,
            )
        grades.append(result)
        spent += result.cost_usd or 0.0
        if spent > cap_usd:
            return grades, True
    return grades, False


VERDICTS: tuple[str, ...] = ("correct", "partly", "wrong", "abstained", "asked")
SUPPORT: tuple[str, ...] = ("yes", "partly", "no", "n/a")


def summary(graded: list[tuple[LlmGrade, str]], *, title: str) -> str:
    """The LLM grades as a page: verdicts per use, support on text answers, disagreements.

    `graded` pairs each LLM grade with the row's deterministic outcome. Disagreements are listed
    both ways: a row the deterministic grader failed that the LLM grader calls correct, and a row
    it passed that the LLM grader does not.
    """
    lines = [f"# LLM grades: {title}", ""]
    if graded:
        first = graded[0][0]
        cost = sum(g.cost_usd or 0.0 for g, _ in graded)
        lines += [
            f"Model {first.model}, prompt version {first.prompt_version}; "
            f"{sum(1 for g, _ in graded if g.cached)} of {len(graded)} from the cache; "
            f"new cost ${cost:.6f}.",
            "",
        ]
    lines += ["| Use | Rows | " + " | ".join(VERDICTS) + " | Errors |", "|---|" + "---:|" * 7]
    for use in ("text", "also accept", "second opinion"):
        part = [g for g, _ in graded if g.use == use]
        counts = [sum(1 for g in part if g.verdict == v) for v in VERDICTS]
        errors = sum(1 for g in part if g.error)
        lines.append(f"| {use} | {len(part)} | " + " | ".join(map(str, counts)) + f" | {errors} |")
    text = [g for g, _ in graded if g.use == "text"]
    lines += ["", "Support on text answers:", "", "| " + " | ".join(SUPPORT) + " |"]
    lines += [
        "|" + "---:|" * 4,
        "| " + " | ".join(str(sum(1 for g in text if g.supported == s)) for s in SUPPORT) + " |",
    ]
    second = [(g, det) for g, det in graded if g.use == "second opinion" and g.verdict]
    disagree = [(g, det) for g, det in second if g.verdict == "correct" and det != "correct"]
    other_way = [(g, det) for g, det in second if g.verdict != "correct" and det == "correct"]
    lines += ["", "## Disagreements", ""]
    if not disagree:
        lines.append(
            "None: no row the deterministic grader failed is called correct by the LLM grader."
        )
    else:
        lines += ["| Row | Deterministic | LLM | Reason |", "|---|---|---|---|"]
        lines += [
            f"| {g.id} #{g.repeat} | {det} | {g.verdict} | {g.reason} |" for g, det in disagree
        ]
    if other_way:
        lines += [
            "",
            "Rows the deterministic grader passed and the LLM grader does not:",
            "",
            "| Row | Deterministic | LLM | Reason |",
            "|---|---|---|---|",
        ]
        lines += [
            f"| {g.id} #{g.repeat} | {det} | {g.verdict} | {g.reason} |" for g, det in other_way
        ]
    decided = [(g, det) for g, det in graded if g.use == "also accept"]
    if decided:  # rows whose also_accept note the LLM grader decides: its verdict is the grade
        lines += ["", "## Decided by the LLM grader (an also_accept note)", ""]
        lines += ["| Row | Deterministic | LLM | Reason |", "|---|---|---|---|"]
        lines += [
            f"| {g.id} #{g.repeat} | {det} | {g.verdict} | {g.reason} |" for g, det in decided
        ]
    return "\n".join(lines) + "\n"
