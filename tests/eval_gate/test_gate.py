"""The deterministic gate (make eval-smoke): 21 scripted agent runs with the checks on.

Each scenario in scenarios.yaml runs the real agent graph, the real checks, the real lookup
and the real grader, with FakeChat in place of the model. The facts come from the facts
table's file when it is present (locally) and from the committed fixture otherwise (CI). No
database, no network.
"""

import json
import time
from pathlib import Path

import pytest

import filingcheck.facts.lookup as lookup_module
from filingcheck.eval.gate import (
    FIXTURE,
    FIXTURE_FIELDS,
    Scenario,
    facts_source,
    load_scenarios,
    run_scenario,
    write_fixture,
)
from filingcheck.facts.lookup import FactsSource
from filingcheck.facts.metrics import METRICS, all_candidate_tags
from filingcheck.paths import DATA_DIR

SCENARIOS = load_scenarios()
BY_ID = {s.id: s for s in SCENARIOS}
REAL_FACTS = DATA_DIR / "facts.jsonl"


@pytest.fixture(scope="module")
def facts() -> FactsSource:
    return facts_source()


@pytest.fixture(scope="module")
def fixture_facts() -> FactsSource:
    return facts_source(facts_file=FIXTURE)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
def test_each_scenario_gives_its_expected_result(scenario: Scenario, facts: FactsSource) -> None:
    assert run_scenario(scenario, facts) == scenario.expected


def test_the_fixture_alone_gives_every_expected_result(fixture_facts: FactsSource) -> None:
    for scenario in SCENARIOS:
        assert run_scenario(scenario, fixture_facts) == scenario.expected, scenario.id


def test_there_are_24_scenarios_covering_what_the_gate_must_cover() -> None:
    assert len(SCENARIOS) == 24
    assert len({s.id for s in SCENARIOS}) == 24
    seen = {o for s in SCENARIOS for o in s.expected.overrides}
    for record in [
        "company:pass",
        "company:repair",
        "company:reject",
        "fiscal_year:pass",
        "fiscal_year:repair",
        "fiscal_year:reject",
        "metric:pass",
        "metric:reject",
        "units:pass",
        "segment:pass",
        "segment:reject",
        "retry:reject",
    ]:
        assert record in seen, record
    assert any(s.expected.requested_scale for s in SCENARIOS)
    assert any(len(s.expected.tool_arguments) == 2 for s in SCENARIOS)  # two companies
    assert any(s.page.ticker for s in SCENARIOS)  # a page-filter question
    golden = {"gate-001", "gate-002", "gate-003", "gate-004"}
    assert golden <= {s.id for s in SCENARIOS}


def test_the_golden_scenarios_return_the_hand_read_values() -> None:
    import yaml

    hand = yaml.safe_load((Path(__file__).parents[1] / "golden_facts.yaml").read_text("utf-8"))
    wanted = {(f["ticker"], f["fiscal_year"], str(f["value"])) for f in hand["facts"]}
    got = {
        (s.expected.tool_arguments[0]["ticker"], s.expected.tool_arguments[0]["fiscal_year"], v)
        for s in SCENARIOS[:4]
        for v in s.expected.values
    }
    assert got == wanted


def test_every_fixture_row_names_its_filing_and_concept() -> None:
    rows = [json.loads(x) for x in FIXTURE.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert rows
    for row in rows:
        assert set(row) == set(FIXTURE_FIELDS)
        assert row["accession"] and row["concept"] and row["dimensions"] == {}


@pytest.mark.skipif(not REAL_FACTS.exists(), reason="the facts table's file is not present")
def test_the_fixture_has_every_candidate_tags_rows_of_every_filing_it_holds() -> None:
    # A wrong tag order must reach the same wrong row on the fixture as on the real file, so
    # for each filing the fixture keeps the no-dimension rows of every candidate tag.
    fixture = [json.loads(x) for x in FIXTURE.read_text(encoding="utf-8").splitlines() if x.strip()]
    filings = {r["accession"] for r in fixture}
    tags = set(all_candidate_tags())
    real = []
    with REAL_FACTS.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if not row["dimensions"] and row["accession"] in filings and row["concept"] in tags:
                real.append({k: row[k] for k in FIXTURE_FIELDS})
    key = lambda r: json.dumps(r, sort_keys=True)  # noqa: E731
    assert sorted(fixture, key=key) == sorted(real, key=key)


def test_writing_the_fixture_from_the_fixture_gives_the_same_file(tmp_path: Path) -> None:
    out = tmp_path / "fixture.jsonl"
    count = write_fixture(SCENARIOS, FIXTURE, out)
    assert out.read_text(encoding="utf-8") == FIXTURE.read_text(encoding="utf-8")
    assert count == len(FIXTURE.read_text(encoding="utf-8").splitlines())


def differs(scenario: Scenario, facts: FactsSource) -> bool:
    """True if the scenario no longer gives its expected result (an error counts)."""
    try:
        return run_scenario(scenario, facts) != scenario.expected
    except Exception:
        return True


def sources(fixture_facts: FactsSource, facts: FactsSource) -> list[FactsSource]:
    """The fixture, and the facts table's file when it is present."""
    return [fixture_facts, facts] if REAL_FACTS.exists() else [fixture_facts]


def test_a_lookup_that_ignores_the_bank_revenue_rule_fails_the_gate(
    monkeypatch: pytest.MonkeyPatch, fixture_facts: FactsSource, facts: FactsSource
) -> None:
    every = sources(fixture_facts, facts)
    monkeypatch.setattr(lookup_module, "candidate_tags", lambda metric, rule: METRICS[metric].tags)
    for facts in every:
        assert differs(BY_ID["gate-004"], facts)  # American Express, a bank-rule company


def test_a_lookup_that_takes_any_period_length_fails_the_gate(
    monkeypatch: pytest.MonkeyPatch, fixture_facts: FactsSource, facts: FactsSource
) -> None:
    every = sources(fixture_facts, facts)
    monkeypatch.setattr(lookup_module, "ANNUAL_DAYS", range(0, 10_000))
    for facts in every:
        assert differs(BY_ID["gate-021"], facts)  # JNJ FY2023 also has a 90-day Q4


def test_the_gate_runs_in_under_10_seconds(fixture_facts: FactsSource) -> None:
    start = time.perf_counter()
    for scenario in SCENARIOS:
        run_scenario(scenario, fixture_facts)
    assert time.perf_counter() - start < 10
