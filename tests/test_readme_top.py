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
    """The README block that starts with the bold title, up to the next bold title or heading."""
    start = README.index(f"\n**{title}**")
    ends = [i for i in (README.find("\n**", start + 1), README.find("\n## ", start + 1)) if i > 0]
    return README[start : min(ends)]


def section(title: str) -> str:
    """The README's "## title" section, to the next heading or bold lead, as the page reads it."""
    start = README.index(f"\n## {title}\n")
    ends = [i for i in (README.find("\n## ", start + 1), README.find("\n**", start + 1)) if i > 0]
    return README[start : min(ends, default=len(README))]


def rows() -> dict[str, str]:
    """The "By the numbers" table: part name to text."""
    found = re.findall(r"^\| ([^|]+?) \| (.+?) \|$", block("By the numbers"), re.MULTILINE)
    return {name: text for name, text in found if name != "Part"}


def find(pattern: str, text: str) -> re.Match[str]:
    """The pattern's match in the text; fails the test if there is none."""
    match = re.search(pattern, text)
    assert match, f"{pattern!r} not in {text!r}"
    return match


WHY = (
    '**Why:** in finance a confident wrong number is worse than "I don\'t know". Asked "How much '
    'net revenue did Morgan report last year?", a plain retrieval-augmented answer picked Morgan '
    "Stanley without asking and gave its fiscal 2023 figure, though the latest report is for 2025 "
    "([baseline answers](docs/baseline_examples.md))."
)
SHOWS = [
    "Its own data, built from raw SEC EDGAR files, because no public dataset covers these filings.",
    "A working agent with three typed tools, and a live demo.",
    "Six server-side checks on the model's number lookups and searches: each call is passed, "
    "repaired or rejected before it runs.",
    "A pre-registered, reproducible evaluation on sealed held-out questions.",
    "A deployed service, with unit and integration tests and 4 CI jobs on every push.",
]
CHECKS_MATTER = (
    "The checks add enforcement that does not depend on the model following instructions, and a "
    "log of every decision; on these questions that did not make the answers more accurate."
)
RECORDS = (
    "Every design decision, with its alternatives and evidence, is in "
    "[docs/decisions.md](docs/decisions.md); each claim with the file that proves it is in "
    "[docs/evidence.md](docs/evidence.md)."
)


def test_the_table_has_the_page_tiles_then_the_three_more_lines() -> None:
    assert list(rows()) == [
        "Data",
        "Numbers",
        "Agent",
        "Checks",
        "Evaluation",
        "Engineering",
        "Cost",
        "CI gate",
        "Reproduction",
    ]
    # Coverage and the figures not compared stay in the facts pages; the Numbers row links one.
    assert "(docs/facts_report.md)" in rows()["Numbers"]


def test_data_is_the_pinned_manifest_downloaded_from_edgar_and_split_into_passages() -> None:
    filings = json.loads(read("data/manifest.json"))["filings"]
    m = find(
        r"^(\d+) annual reports \(10-Ks\) from (\d+) companies, (\d+) years each, downloaded from "
        r"SEC EDGAR, pinned by accession number and split into ([\d,]+) passages, searched by "
        r"meaning and by keyword\.$",
        rows()["Data"],
    )
    years: dict[str, set[int]] = {}
    for f in filings:
        years.setdefault(f["ticker"], set()).add(f["fiscal_year"])
    assert number(m[1]) == len(filings)
    assert number(m[2]) == len(years)
    assert {len(held) for held in years.values()} == {number(m[3])}
    assert all(re.fullmatch(r"\d{10}-\d{2}-\d{6}", f["accession"]) for f in filings)
    assert number(m[4]) == number(find(r"\| Chunks \| ([\d,]+) \|", read("docs/data_report.md"))[1])
    # Downloaded from EDGAR: the filings client reads each document from the SEC's archive.
    assert "https://www.sec.gov/Archives/edgar/data/" in read("filingcheck/ingest/filings.py")


def test_numbers_are_the_metric_map_and_the_companyfacts_cross_check() -> None:
    m = find(
        r"^(\d+) financial metrics .*; ([\d,]+) figures cross-checked .*, (\d+) disagreements",
        re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", rows()["Numbers"]),  # read past the link
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


def test_evaluation_is_the_committed_final_rows() -> None:
    files = sorted((ROOT / "eval/results").glob("2026-11-14_*-final.jsonl"))
    answers = sum(
        1 for f in files for line in f.read_text(encoding="utf-8").splitlines() if line.strip()
    )
    setups = {f.name.removesuffix("-final.jsonl").rsplit("_", 1)[1] for f in files}
    m = find(r"^([\d,]+) test answers across (\d+) setups", rows()["Evaluation"])
    assert (number(m[1]), number(m[2])) == (answers, len(setups))


def test_engineering_is_the_ci_jobs_and_the_deploy_files() -> None:
    assert rows()["Engineering"] == (
        "Unit and integration tests and 4 CI jobs on every push; a FastAPI service in Docker on "
        "Render, Postgres + pgvector on Neon, the page on Vercel."
    )
    ci = yaml.safe_load(read(".github/workflows/ci.yml"))
    assert len(ci["jobs"]) == number(find(r"and (\d+) CI jobs", rows()["Engineering"])[1])
    assert "integration" in ci["jobs"]
    assert {"push", "pull_request"} <= set(ci[True])  # YAML reads the key "on" as true
    assert "FastAPI(" in read("filingcheck/app/api.py")
    assert "uvicorn filingcheck.app.main:app" in read("Dockerfile")
    render = read("render.yaml")
    assert "runtime: docker" in render and "Neon" in render
    assert "filingcheck.vercel.app" in README


def test_cost_is_the_final_reports_checks_on_cost_per_100_held_out_questions() -> None:
    start = REPORT.index("\n### held-out\n")
    held_out = REPORT[start : REPORT.index("\n### ", start + 1)]
    row = find(r"(?m)^\| agent-checks-on \| (\d+) \| \d+ \| .* \| \$([\d.]+) \|$", held_out)
    assert number(row[1]) == 110
    stated = find(
        r"^About \$([\d.]+) per 100 questions with the checks on, in the final run\.$",
        rows()["Cost"],
    )
    assert f"{float(row[2]):.2f}" == stated[1]


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
        "docs/what_works_today.md": r"A deterministic gate in CI:\*\* (\d+) scripted scenarios",
    }
    for path, pattern in stated.items():
        assert number(find(pattern, read(path))[1]) == count, path


def test_reproduction_names_make_report() -> None:
    assert "`make report`" in rows()["Reproduction"]


def test_what_this_project_shows_is_five_lines_with_no_effect_claim_and_no_figures() -> None:
    lines = [
        line[2:] for line in block("What this project shows").splitlines() if line.startswith("- ")
    ]
    assert lines == SHOWS
    joined = " ".join(lines)
    assert not re.search(r"cut|better|fewer|reduc|improv|accura", joined, re.IGNORECASE)
    # The figures live in "By the numbers"; the one count here is the CI jobs, said as there.
    assert re.findall(r"\d[\d,.%]*", joined) == ["4"]
    assert "4 CI jobs on every push" in rows()["Engineering"]


def test_the_why_line_sits_under_the_description_and_is_the_saved_baseline_answer() -> None:
    lines = [line for line in README.splitlines() if line.strip()]
    assert lines[1].startswith("An agent that answers questions")
    assert lines[2] == WHY
    baseline = read("docs/baseline_examples.md")
    assert "plain RAG, no agent, no checks" in baseline
    entry = baseline[
        baseline.index("## trap-001: How much net revenue did Morgan report last year?") :
    ]
    answer = next(line for line in entry.splitlines() if line.startswith("> "))
    assert "Morgan Stanley" in answer and "fiscal year ended December 31, 2023" in answer
    assert "?" not in answer  # it answered without asking which Morgan
    filings = json.loads(read("data/manifest.json"))["filings"]
    assert max(f["fiscal_year"] for f in filings if f["ticker"] == "MS") == 2025


def test_no_test_count_is_stated() -> None:
    count = r"\d[\d,]*\s+(?:[a-z]+\s+)?tests\b|\d[\d,]*\s+test (?:functions|cases)"
    for path in (
        "README.md",
        "docs/what_works_today.md",
        "docs/known_limits.md",
        "web/lib/glance.ts",
        "web/app/page.tsx",
    ):
        assert not re.search(count, read(path)), path


def test_the_additions_sit_above_the_results() -> None:
    result = README.index("\n## Results\n")
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


def test_results_is_one_short_section_that_opens_with_the_prompt_rules_result() -> None:
    results = section("Results")
    assert README.count("\n## Results\n") == 1
    assert "**The result**" not in README and "## What the measurement showed" not in README
    lines = [line for line in results.strip().splitlines()[1:] if line.strip()]
    # The first claim is the prompt-rules result with its interval; nothing comes before it.
    assert lines[0].startswith(
        "- **The same rules written into the model's prompt were more accurate than enforcing "
        "them on the server:**"
    )
    assert (
        "85.2% against 75.5%" in lines[0] and "-9.7 points, 95% interval -16.4 to -3.0" in lines[0]
    )
    # The README's own sentence on why the checks matter ends the first claim.
    assert lines[0].endswith(" " + CHECKS_MATTER)
    bullets = [line for line in lines if line.startswith("- ")]
    assert len(bullets) == 4
    assert "18.5% to 10.6%" in bullets[1] and "-12.7 to -3.6" in bullets[1]
    assert "of 90 failed checks-on runs" in bullets[2]
    assert "23 came from gaps in the checks and 17 from a check's own action" in bullets[2]
    assert "18% to 29%" in bullets[3]
    assert lines[4] == next(line for line in lines if line.startswith("![")), "then the chart"
    assert "(docs/results/final_summary.png)" in lines[4]
    after = " ".join(lines[5:])
    assert len(re.findall(r"[.!?](?:\s|$)", after)) <= 3
    assert "(eval/PREREGISTRATION.md)" in after
    assert "(eval/results/2026-11-14_final_report.md)" in after
    assert "make report" in after
    # About 200 words as read: the chart's alt text and the link targets are not counted.
    shown = "\n".join(line for line in results.splitlines() if not line.startswith("!["))
    words = len(re.sub(r"\]\([^)]*\)|[*`#\[\]!]", " ", shown).split())
    assert 170 <= words <= 230, words
    assert "final_rates.png" not in README


def test_after_results_every_section_is_a_heading_so_github_ends_results_there() -> None:
    results = README.index("\n## Results\n")
    # Bold leads come only above the results; below them every section has a "##" heading.
    for line in README.splitlines():
        if line.startswith("**"):
            assert README.index(line) < results, line[:60]
    after = README[results + 1 :].splitlines()[1:]
    assert next(line for line in after if line.startswith(("## ", "**"))) == "## How it is built"


def test_the_two_build_sections_open_with_whole_sentences() -> None:
    built = [line for line in section("How it is built").splitlines() if line.strip()]
    assert built[1] == "The diagram's source is [docs/architecture.mmd](docs/architecture.mmd)."
    one = [
        line for line in section("How one question goes through it").splitlines() if line.strip()
    ]
    assert one[1] == (
        'From the saved example "How much revenue did Nike make last year?" '
        "(`web/data/examples.json`; the page shows it):"
    )


def test_known_limits_has_the_eight_and_links_all_sixteen() -> None:
    limits = section("Known limits")
    mine = [line[2:] for line in limits.splitlines() if line.startswith("- ")]
    assert len(mine) == 8
    assert "[All known limits](docs/known_limits.md)" in limits
    page = read("docs/known_limits.md")
    everything = [line[2:] for line in page.splitlines() if line.startswith("- ")]
    assert len(everything) == 16
    # Each of the eight is one of the sixteen, word for word or cut short at a sentence's end.
    for limit in mine:
        assert any(full.startswith(limit) for full in everything), limit[:60]
    for words in (
        "One model was measured",
        "The intervals are wide",
        "miss phrasings",
        "cover the arguments of the tools",
        "Verified means",
        "The graders are automatic",
        "gold values come from the same lookup",
        "In an answer with a calculation",
    ):
        assert sum(words in limit for limit in mine) == 1, words


def test_what_works_today_moved_to_its_own_page_linked_once() -> None:
    assert "## What works today" not in README
    assert README.count("(docs/what_works_today.md)") == 1
    page = read("docs/what_works_today.md")
    assert page.startswith("# What works today")
    assert len([line for line in page.splitlines() if line.startswith("- **")]) >= 10


def test_reproduce_is_the_two_commands_and_two_sentences_then_the_records_line() -> None:
    reproduce = section("Reproduce the results")
    assert "make setup" in reproduce and "make report" in reproduce
    assert [line for line in reproduce.splitlines() if line.strip()][-1] == RECORDS
    assert (ROOT / "docs/decisions.md").is_file() and (ROOT / "docs/evidence.md").is_file()
    reproduce = reproduce.replace(RECORDS, "")
    prose = re.sub(r"```.*?```", " ", reproduce, flags=re.S).replace("## Reproduce the results", "")
    assert len(re.findall(r"[.!?](?:\s|$)", prose.strip())) == 2
    assert "make verify-measured" in prose
    assert len(reproduce.split()) <= 110


def test_the_readme_is_about_1600_words() -> None:
    assert len(README.split()) <= 1700, len(README.split())


def test_known_limits_page_says_the_control_questions_were_seen_in_development() -> None:
    assert (
        "- The control questions were used during development: the fiscal-year check on searches "
        "was built after a dry run on them (decisions, Nov 12), so the rise in control accuracy "
        "is not held-out evidence." in read("docs/known_limits.md")
    )


def test_known_limits_says_a_figure_rewritten_in_the_working_is_unverified() -> None:
    limits = section("Known limits")
    assert (
        "- In an answer with a calculation, a figure the model writes again in its working (for "
        'example "130,497 M") is labeled Unverified, because the labeler reads figures as written.'
        in limits
    )
