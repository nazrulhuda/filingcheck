"""The deterministic gate (make eval-smoke): 20 scripted agent runs with the checks on.

Each scenario in scenarios.yaml runs the real agent graph, the real checks, the real lookup
and the real grader, with FakeChat in place of the model. The facts come from the facts
table's file when it is present (locally) and from the committed fixture otherwise (CI). No
database, no network.
"""

import json
import time
from pathlib import Path

import pytest

from filingcheck.eval.gate import (
    FIXTURE,
    FIXTURE_FIELDS,
    Scenario,
    facts_source,
    load_scenarios,
    run_scenario,
)
from filingcheck.facts.lookup import FactsSource
from filingcheck.paths import DATA_DIR

SCENARIOS = load_scenarios()
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


def test_there_are_20_scenarios_covering_what_the_gate_must_cover() -> None:
    assert len(SCENARIOS) == 20
    assert len({s.id for s in SCENARIOS}) == 20
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
def test_the_fixture_rows_are_the_facts_tables_rows() -> None:
    fixture = [json.loads(x) for x in FIXTURE.read_text(encoding="utf-8").splitlines() if x.strip()]
    pairs = {(r["accession"], r["concept"]) for r in fixture}
    real = []
    with REAL_FACTS.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if not row["dimensions"] and (row["accession"], row["concept"]) in pairs:
                real.append({k: row[k] for k in FIXTURE_FIELDS})
    key = lambda r: json.dumps(r, sort_keys=True)  # noqa: E731
    assert sorted(fixture, key=key) == sorted(real, key=key)


def test_the_gate_runs_in_under_10_seconds(fixture_facts: FactsSource) -> None:
    start = time.perf_counter()
    for scenario in SCENARIOS:
        run_scenario(scenario, fixture_facts)
    assert time.perf_counter() - start < 10
