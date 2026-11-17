"""The README's top: every figure in "By the numbers" matches the file it comes from, the additions
sit above the results without changing them, and the gate's scenario count is the same wherever
it is stated."""

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
REPORT = (ROOT / "eval/results/2026-11-14_final_report.md").read_text(encoding="utf-8")


def read(path: str) -> str:
    """A repository file's text."""
    return (ROOT / path).read_text(encoding="utf-8")


def number(text: str) -> int:
    """A figure as written, with its thousands commas."""
    return int(text.replace(",", ""))


def block(title: str) -> str:
    """The README block that starts with the bold title, up to the next bold title."""
    start = README.index(f"\n**{title}**")
    end = README.index("\n**", start + 1)
    return README[start:end]


def rows() -> dict[str, str]:
    """The "By the numbers" table: part name to text."""
    found = re.findall(r"^\| ([^|]+?) \| (.+?) \|$", block("By the numbers"), re.MULTILINE)
    return {name: text for name, text in found if name != "Part"}


def find(pattern: str, text: str) -> re.Match[str]:
    """The pattern's match in the text; fails the test if there is none."""
    match = re.search(pattern, text)
    assert match, f"{pattern!r} not in {text!r}"
    return match


def test_the_table_has_the_page_tiles_then_the_four_more_lines() -> None:
    assert list(rows()) == [
        "Data",
        "Search",
        "Numbers",
        "Agent",
        "Checks",
        "Testing",
        "Coverage",
        "Not compared",
        "CI gate",
        "Reproduction",
    ]


def test_data_is_the_pinned_manifest() -> None:
    filings = json.loads(read("data/manifest.json"))["filings"]
    m = find(
        r"^(\d+) annual reports \(10-Ks\) from (\d+) companies, (\d+) years each", rows()["Data"]
    )
    years: dict[str, set[int]] = {}
    for f in filings:
        years.setdefault(f["ticker"], set()).add(f["fiscal_year"])
    assert number(m[1]) == len(filings)
    assert number(m[2]) == len(years)
    assert {len(held) for held in years.values()} == {number(m[3])}
    assert all(re.fullmatch(r"\d{10}-\d{2}-\d{6}", f["accession"]) for f in filings)


def test_search_is_the_data_reports_passages_from_those_items() -> None:
    m = find(r"^([\d,]+) passages from Items 1, 1A, 7, 7A and 8 of each report", rows()["Search"])
    assert number(m[1]) == number(find(r"\| Chunks \| ([\d,]+) \|", read("docs/data_report.md"))[1])
    sections = json.loads(read("data/section_snapshot.json"))
    items = {re.sub(r"^\S+ FY\d{4} Item ", "", name) for name in sections}
    assert items == {
        "1",
        "1A",
        "7",
        "7A",
        "8",
        "1-7A",
    }  # 1-7A: Items a filing's index keeps together


def test_numbers_are_the_metric_map_and_the_companyfacts_cross_check() -> None:
    m = find(
        r"^(\d+) financial metrics .*; ([\d,]+) figures cross-checked .*, (\d+) disagreements",
        rows()["Numbers"],
    )
    assert number(m[1]) == len(
        re.findall(r'MetricSpec\(\s*"', read("filingcheck/facts/metrics.py"))
    )
    facts = read("docs/facts_report.md")
    assert number(m[2]) == number(find(r"- Agreements: ([\d,]+)", facts)[1])
    assert number(m[3]) == number(find(r"- Disagreements: ([\d,]+)", facts)[1])


def test_agent_and_checks_are_the_tool_registry_and_the_reports_check_table() -> None:
    tools = re.findall(r'Tool\(\s*"([a-z_]+)"', read("filingcheck/tools/__init__.py"))
    assert tools == ["search_filings", "get_financial_fact", "calculate"]
    assert number(find(r"^(\d+) tools", rows()["Agent"])[1]) == len(tools)
    pairs = set(
        re.findall(
            r"^\| [a-z_]+ \| [a-z_]+ \| (get_financial_fact|search_filings) \| ([a-z_]+) \|",
            REPORT,
            re.MULTILINE,
        )
    )
    assert number(find(r"^(\d+) server-side rules", rows()["Checks"])[1]) == len(pairs)


def test_testing_is_the_committed_final_rows() -> None:
    files = sorted((ROOT / "eval/results").glob("2026-11-14_*-final.jsonl"))
    answers = sum(
        1 for f in files for line in f.read_text(encoding="utf-8").splitlines() if line.strip()
    )
    setups = {f.name.removesuffix("-final.jsonl").rsplit("_", 1)[1] for f in files}
    m = find(r"^([\d,]+) test answers across (\d+) setups", rows()["Testing"])
    assert (number(m[1]), number(m[2])) == (answers, len(setups))


def test_coverage_is_the_coverage_pages_totals_and_nothing_is_derived() -> None:
    coverage = read("docs/facts_coverage.md")
    found = [(number(a), number(b)) for a, b in re.findall(r"\| (\d+) of (\d+) \|", coverage)]
    assert len(found) == 13
    m = find(r"^([\d,]+) of ([\d,]+) company-year metric values", rows()["Coverage"])
    assert number(m[1]) == sum(a for a, _ in found)
    assert number(m[2]) == sum(b for _, b in found)
    assert '"unavailable"' in rows()["Coverage"] and "derives nothing" in rows()["Coverage"]
    assert "Nothing is derived." in coverage


def test_not_compared_is_the_facts_reports_count_all_from_one_filing() -> None:
    facts = read("docs/facts_report.md")
    m = find(r"^(\d+) figures had no companyfacts entry to compare", rows()["Not compared"])
    assert number(m[1]) == number(find(r"- Not in companyfacts: ([\d,]+)", facts)[1])
    missing = re.findall(
        r"^\| (\w+) \| (\d{4}) \| `[^`]+` \| [^|]+ \| not in companyfacts \|", facts, re.M
    )
    assert len(missing) == number(m[1])
    assert set(missing) == {("SPGI", "2024")}
    assert "S&P Global's fiscal 2024 filing" in rows()["Not compared"]


def test_the_gate_count_is_the_scenario_files_wherever_it_is_stated() -> None:
    scenarios = yaml.safe_load(read("tests/eval_gate/scenarios.yaml"))["scenarios"]
    count = len(scenarios)
    assert number(find(r"^(\d+) scripted agent scenarios", rows()["CI gate"])[1]) == count
    header = r"The deterministic gate \(make eval-smoke\): (\d+) scripted"
    stated = {
        "Makefile": r"the deterministic gate: (\d+) scripted agent runs",
        ".github/workflows/ci.yml": r"The deterministic gate \((\d+) scripted scenarios",
        "eval/README.md": r"Each of the (\d+) scenarios in `tests/eval_gate/scenarios.yaml`",
        "tests/eval_gate/scenarios.yaml": "^# " + header,
        "tests/eval_gate/test_gate.py": '^"""' + header,
        "README.md": r"A deterministic gate in CI:\*\* (\d+) scripted scenarios",
    }
    for path, pattern in stated.items():
        assert number(find(pattern, read(path))[1]) == count, path


def test_reproduction_names_make_report() -> None:
    assert "`make report`" in rows()["Reproduction"]


def test_what_this_project_shows_is_three_lines_with_no_effect_claim() -> None:
    lines = [
        line for line in block("What this project shows").splitlines() if line.startswith("- ")
    ]
    assert len(lines) == 3
    assert not re.search(r"cut|better|fewer|reduc|improv|accura", " ".join(lines), re.IGNORECASE)


def test_the_additions_sit_above_the_results_which_still_lead_with_the_prompt_rules() -> None:
    result = README.index("\n**The result**")
    title_end = README.index("\n\n", README.index("# FilingCheck\n\n") + len("# FilingCheck\n\n"))
    shot = README.index("![", title_end)
    assert shot < README.index("**Live demo:") < result
    assert README[shot:].startswith("![The live page")
    assert "(docs/page_saved_example.png)" in README[shot:result]
    assert (ROOT / "docs/page_saved_example.png").is_file()
    for title in ("What this project shows", "By the numbers"):
        assert README.index(f"\n**{title}**") < result
    top = README[:result]
    assert re.search(r"<!-- [^>]*video[^>]*-->", top, re.IGNORECASE)
    assert top.count("![") == 2  # the screenshot and the CI badge; no badge images for the stack
    assert (
        "Built with Python, LangGraph, FastAPI, Postgres + pgvector, Next.js/TypeScript, Docker, "
        "GitHub Actions." in top
    )
    first = README[result:].split("\n- ", 1)[1]
    assert first.startswith(
        "**The same rules written into the model's prompt were more accurate than enforcing them "
        "on the server.**"
    )


def test_known_limits_says_the_control_questions_were_seen_in_development() -> None:
    limits = README[README.index("## Known limits") : README.index("## What works today")]
    assert (
        "- The control questions were used during development: the fiscal-year check on searches "
        "was built after a dry run on them (decisions, Nov 12), so the rise in control accuracy "
        "is not held-out evidence." in limits
    )
