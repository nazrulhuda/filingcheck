"""The deterministic gate (make eval-smoke): scripted agent runs with the checks on.

A recorded model conversation cannot be replayed honestly once a tool result changes, so the
gate scripts the model instead: each scenario in `tests/eval_gate/scenarios.yaml` gives the
question, the page filters, the model's tool calls and its final answer, and the gate runs
the real agent graph, checks, lookup and grader on them with `FakeChat`. It compares the
override records, the arguments that reach `get_financial_fact`, the values it returns, the
requested scale and the final answer's grade with what the scenario expects.

The facts come from `data/facts.jsonl` (the facts table's file) when it is present, and from
`tests/eval_gate/facts_fixture.jsonl` otherwise (CI). The fixture is written by
`python -m filingcheck.eval gate-fixture`: for every filing the scenarios read, the
no-dimension rows of every candidate tag of every metric, with their accession and concept.
Keeping every candidate tag, not only the ones the correct code read, means a wrong tag
order or a wrong period rule reaches the same wrong row on the fixture as on the real file.
The gate checks the checks' decisions and the tool path; accuracy on real models is
measured by `make eval`.
"""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from filingcheck.agent.graph import run_agent
from filingcheck.checks import reference_data
from filingcheck.eval.grade import grade
from filingcheck.eval.questions import Question
from filingcheck.facts.lookup import FactsSource, FilingRef, JsonlFacts, TotalFact
from filingcheck.facts.metrics import all_candidate_tags
from filingcheck.llm import FakeChat, scripted_tool_calls
from filingcheck.paths import DATA_DIR, REPO_ROOT
from filingcheck.retrieval.models import SearchResult
from filingcheck.tools import ToolDeps

GATE_DIR = REPO_ROOT / "tests" / "eval_gate"
SCENARIOS_FILE = GATE_DIR / "scenarios.yaml"
FIXTURE = GATE_DIR / "facts_fixture.jsonl"
FIXTURE_FIELDS = (
    "accession",
    "ticker",
    "fiscal_year",
    "concept",
    "value",
    "unit",
    "period_start",
    "period_end",
    "instant",
    "decimals",
    "dimensions",
)
FACT_TOOL = "get_financial_fact"


class Call(BaseModel):
    """One tool call the scripted model asks for."""

    model_config = ConfigDict(extra="forbid")

    name: str
    arguments: dict[str, Any]


class Page(BaseModel):
    """The page filters the user set, if any."""

    model_config = ConfigDict(extra="forbid")

    ticker: str | None = None
    fiscal_year: int | None = None


class Result(BaseModel):
    """What a scenario must give: the comparison is exact."""

    model_config = ConfigDict(extra="forbid")

    overrides: list[str]  # "check:outcome", in order, across all calls
    tool_arguments: list[dict[str, Any]]  # what reached get_financial_fact, in order
    search_arguments: list[dict[str, Any]] = []  # what reached search_filings, in order
    values: list[str]  # what those calls returned, raw units
    requested_scale: str | None = None
    grade: str


class Scenario(BaseModel):
    """One scripted agent run and its expected result."""

    model_config = ConfigDict(extra="forbid")

    id: str
    covers: str
    question: str
    page: Page = Field(default_factory=Page)
    turns: list[list[Call]]  # one model turn each; a turn may ask for several calls
    final_answer: str
    grade_as: dict[str, Any]  # the question fields the grader needs
    expected: Result


def load_scenarios(path: Path = SCENARIOS_FILE) -> list[Scenario]:
    """The scenarios of the gate, in file order."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [Scenario.model_validate(s) for s in data["scenarios"]]


class NoRetriever:
    """The gate's scenarios never search the text; a search finds nothing."""

    name = "none"

    def search(
        self,
        query: str,
        *,
        ticker: str | None = None,
        fiscal_year: int | None = None,
        items: list[str] | None = None,
        k: int = 10,
    ) -> SearchResult:
        """No hits."""
        return SearchResult(hits=[], retriever=self.name)


class RecordingFacts:
    """A facts source that remembers every filing it was asked about."""

    def __init__(self, inner: FactsSource) -> None:
        self.inner = inner
        self.read: set[str] = set()  # accessions

    def filing(self, ticker: str, fiscal_year: int) -> FilingRef | None:
        """The inner source's filing."""
        return self.inner.filing(ticker, fiscal_year)

    def facts(self, accession: str, concepts: Sequence[str]) -> list[TotalFact]:
        """The inner source's facts; the filing is recorded."""
        self.read.add(accession)
        return self.inner.facts(accession, concepts)


def facts_source(facts_file: Path | None = None) -> JsonlFacts:
    """The facts table's file when present, else the gate's fixture."""
    if facts_file is None:
        real = DATA_DIR / "facts.jsonl"
        facts_file = real if real.exists() else FIXTURE
    return JsonlFacts(DATA_DIR / "manifest.json", DATA_DIR / "companies.yaml", facts_file)


def run_scenario(scenario: Scenario, facts: FactsSource) -> Result:
    """Run one scenario through the agent with the checks on, and say what came out."""
    replies: list[Any] = [
        scripted_tool_calls(*[(c.name, c.arguments) for c in turn]) for turn in scenario.turns
    ]
    chat = FakeChat([*replies, scenario.final_answer])
    deps = ToolDeps(retriever=NoRetriever(), facts=facts, **reference_data())
    answer = run_agent(
        scenario.question,
        model=chat,
        deps=deps,
        ticker=scenario.page.ticker,
        fiscal_year=scenario.page.fiscal_year,
        checks=True,
    )
    scales = [
        (json.loads(m["content"]).get("requested_scale") or {}).get("value")
        for call in chat.calls
        for m in call["messages"]
        if m["role"] == "tool" and m["content"].startswith("{")
    ]
    fields = {"id": scenario.id, "question": scenario.question, **scenario.grade_as}
    if fields.get("gold_value") is not None:  # every gold value here is a USD fact
        fields = {"gold_unit": "USD", "gold_source": "facts", **fields}
    question = Question.model_validate(fields)
    return Result(
        overrides=[f"{o.check}:{o.outcome}" for o in answer.overrides],
        tool_arguments=[
            r.arguments for r in answer.tool_calls if r.name == FACT_TOOL and r.status == "ok"
        ],
        search_arguments=[
            r.arguments
            for r in answer.tool_calls
            if r.name == "search_filings" and r.status == "ok"
        ],
        values=[str(f.value) for f in answer.facts_used],
        requested_scale=next((s for s in scales if s), None),
        grade=grade({"answer": answer.text, "error": None}, question).outcome,
    )


def write_fixture(
    scenarios: Sequence[Scenario], facts_file: Path = DATA_DIR / "facts.jsonl", out: Path = FIXTURE
) -> int:
    """Write every candidate tag's rows of each filing the scenarios read; return how many."""
    recorder = RecordingFacts(facts_source(facts_file))
    for scenario in scenarios:
        run_scenario(scenario, recorder)
    tags = set(all_candidate_tags())
    rows = []
    with facts_file.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["dimensions"] or row["concept"] not in tags:
                continue
            if row["accession"] in recorder.read:
                rows.append({k: row[k] for k in FIXTURE_FIELDS})
    rows.sort(key=lambda r: (r["accession"], r["concept"], json.dumps(r, sort_keys=True)))
    out.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8", newline="\n")
    return len(rows)
