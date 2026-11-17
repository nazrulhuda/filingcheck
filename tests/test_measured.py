"""The measured system is pinned: `make verify-measured` fails on a change under a pinned path,
on a moved tag, and on a changed or new final row or grade file."""

import hashlib
import subprocess
from pathlib import Path

import pytest

from filingcheck.measured import (
    PINNED,
    REWORDED,
    ROWS,
    ROWS_COMMIT,
    TAG,
    TAG_COMMIT,
    Pin,
    changed_files,
    main,
    problems,
    without_paragraph,
)


def git(root: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True, encoding="utf-8"
    )
    return done.stdout.strip()


def repo(tmp_path: Path) -> tuple[Path, str, str]:
    """A repository like ours: the measured commit, tagged; then the rows in a later commit.

    Returns the root, the measured commit and the rows commit.
    """
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "test")
    (tmp_path / "pinned").mkdir()
    (tmp_path / "free").mkdir()
    (tmp_path / "pinned" / "rules.py").write_text("RULE = 1\n", encoding="utf-8")
    (tmp_path / "pinned" / "gold.jsonl").write_text('{"id": "q-1"}\n', encoding="utf-8")
    (tmp_path / "free" / "report.py").write_text("PAGE = 1\n", encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "the measured system")
    git(tmp_path, "tag", TAG)
    measured = git(tmp_path, "rev-parse", "HEAD")
    (tmp_path / "rows").mkdir()
    (tmp_path / "rows" / "2026-11-14_control_agent-checks-on-final.jsonl").write_text(
        '{"id": "control-001", "answer": "x"}\n', encoding="utf-8"
    )
    (tmp_path / "rows" / "2026-11-14_control_agent-checks-on-final_llm.jsonl").write_text(
        '{"id": "control-001", "verdict": "correct"}\n', encoding="utf-8"
    )
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "the final rows")
    return tmp_path, measured, git(tmp_path, "rev-parse", "HEAD")


def pins(measured: str, rows: str) -> tuple[Pin, ...]:
    return (
        Pin(commit=measured, paths=("pinned",), tag=TAG),
        Pin(
            commit=rows,
            paths=("rows/2026-11-14_*-final.jsonl", "rows/2026-11-14_*-final_llm.jsonl"),
        ),
    )


# ---------------------------------------------------------------- the pinned paths


def test_nothing_changed_passes(tmp_path: Path) -> None:
    root, measured, rows = repo(tmp_path)
    assert problems(root, pins(measured, rows)) == []


def test_a_changed_pinned_file_is_named_and_a_changed_free_file_is_not(tmp_path: Path) -> None:
    root, measured, rows = repo(tmp_path)
    (root / "free" / "report.py").write_text("PAGE = 2\n", encoding="utf-8")
    assert problems(root, pins(measured, rows)) == []
    (root / "pinned" / "rules.py").write_text("RULE = 2\n", encoding="utf-8")
    assert changed_files(root, measured, ("pinned",)) == ["pinned/rules.py"]
    [problem] = problems(root, pins(measured, rows))
    assert "pinned/rules.py" in problem and measured[:12] in problem


def test_a_new_file_under_a_pinned_path_counts_as_a_change(tmp_path: Path) -> None:
    root, measured, _ = repo(tmp_path)
    (root / "pinned" / "extra.py").write_text("NEW = 1\n", encoding="utf-8")
    assert changed_files(root, measured, ("pinned",)) == ["pinned/extra.py"]


def test_a_single_pinned_file_is_pinned_on_its_own(tmp_path: Path) -> None:
    root, measured, _ = repo(tmp_path)
    (root / "pinned" / "gold.jsonl").write_text('{"id": "q-2"}\n', encoding="utf-8")
    assert changed_files(root, measured, ("pinned/rules.py",)) == []
    assert changed_files(root, measured, ("pinned/gold.jsonl",)) == ["pinned/gold.jsonl"]


# ---------------------------------------------------------------- a moved tag


def test_a_moved_tag_fails_even_when_the_tree_matches_the_tag(tmp_path: Path) -> None:
    """The review's gap: the tag moved onto a commit that changes a pinned file."""
    root, measured, rows = repo(tmp_path)
    (root / "pinned" / "rules.py").write_text("RULE = 2\n", encoding="utf-8")
    git(root, "commit", "-q", "-am", "a changed check")
    git(root, "tag", "-f", TAG)
    found = problems(root, pins(measured, rows))
    assert any(TAG in p and "points to" in p and measured[:12] in p for p in found)
    assert any("pinned/rules.py" in p for p in found)


# ---------------------------------------------------------------- the final rows


def test_an_edited_final_row_fails(tmp_path: Path) -> None:
    root, measured, rows = repo(tmp_path)
    path = root / "rows" / "2026-11-14_control_agent-checks-on-final.jsonl"
    path.write_text(path.read_text(encoding="utf-8").replace('"x"', '"y"'), encoding="utf-8")
    [problem] = problems(root, pins(measured, rows))
    assert "rows/2026-11-14_control_agent-checks-on-final.jsonl" in problem
    assert rows[:12] in problem


def test_a_new_file_named_like_a_final_row_fails_and_another_name_passes(tmp_path: Path) -> None:
    root, measured, rows = repo(tmp_path)
    (root / "rows" / "notes.md").write_text("notes\n", encoding="utf-8")
    assert problems(root, pins(measured, rows)) == []
    (root / "rows" / "2026-11-14_dev_traps_baseline-final.jsonl").write_text(
        "{}\n", encoding="utf-8"
    )
    [problem] = problems(root, pins(measured, rows))
    assert "rows/2026-11-14_dev_traps_baseline-final.jsonl" in problem


# ---------------------------------------------------------------- the command and the lists


def test_the_command_fails_and_names_the_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, measured, rows = repo(tmp_path)
    assert main(["--root", str(root)], pins=pins(measured, rows)) == 0
    assert "unchanged" in capsys.readouterr().out
    (root / "pinned" / "rules.py").write_text("RULE = 3\n", encoding="utf-8")
    assert main(["--root", str(root)], pins=pins(measured, rows)) == 1
    out = capsys.readouterr().out
    assert "pinned/rules.py" in out and measured[:12] in out


def test_the_pinned_lists_are_the_plans_lists() -> None:
    """The answering code, the grading and scoring code, the data pins, the measured sets,
    and the 50 final row and grade files against the commit that merged them."""
    assert TAG == "week6-measured"
    assert TAG_COMMIT == "da7a451e0a0ab872b2bc3f05a96699690b82d0eb"
    assert ROWS_COMMIT == "4082c4e7ef6ba74a5acee0ad943fbdce06e77049"
    for path in (
        "filingcheck/agent",
        "filingcheck/checks",
        "filingcheck/tools",
        "filingcheck/answer",
        "filingcheck/labels",
        "filingcheck/retrieval",
        "filingcheck/llm",
        "filingcheck/facts",
        "filingcheck/eval/grade.py",
        "filingcheck/eval/llm_grade.py",
        "filingcheck/eval/metrics.py",
        "filingcheck/eval/stats.py",
        "filingcheck/eval/questions.py",
        "eval/grader_prompt.md",
        "data/companies.yaml",
        "data/manifest.json",
        "eval/PREREGISTRATION.md",
        "eval/questions/heldout_traps.jsonl",
        "eval/questions/heldout_traps_2.jsonl",
        "eval/questions/dev_traps.jsonl",
        "eval/questions/dev_unanswerable.jsonl",
        "eval/questions/control.jsonl",
    ):
        assert path in PINNED, path
    assert "eval/questions/page_examples.jsonl" not in PINNED  # Day 46 adds to it
    root = Path(__file__).resolve().parents[1]
    assert all((root / p).exists() for p in PINNED)
    assert ROWS == (
        "eval/results/2026-11-14_*-final.jsonl",
        "eval/results/2026-11-14_*-final_llm.jsonl",
    )
    assert len([p for pattern in ROWS for p in root.glob(pattern)]) == 50


# ---------------------------------------------------------------- the reworded paragraph

MARK = "**Who wrote this and when.**"
NEW_MARK = "**When this was written.**"


def exempt(paragraph: str) -> dict[str, tuple[str, str, str]]:
    """The exemption for the test file: its old lead, its new lead, and the new paragraph's hash."""
    return {"pinned/prereg.md": (MARK, NEW_MARK, hashlib.sha256(paragraph.encode()).hexdigest())}


PREREG = """# Pre-registration

**Who wrote this and when.** Written on day 1.

## Rules

Rule 1: the headline is confidently wrong answers.
"""


def prereg_repo(tmp_path: Path) -> tuple[Path, str]:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "test")
    (tmp_path / "pinned").mkdir()
    (tmp_path / "pinned" / "prereg.md").write_text(PREREG, encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "the pre-registration")
    return tmp_path, git(tmp_path, "rev-parse", "HEAD")


def test_without_paragraph_drops_only_the_marked_paragraph() -> None:
    assert without_paragraph(PREREG, MARK) == (
        "# Pre-registration\n\n## Rules\n\nRule 1: the headline is confidently wrong answers.\n"
    )


def test_a_reworded_first_paragraph_passes_and_any_other_change_fails(tmp_path: Path) -> None:
    root, commit = prereg_repo(tmp_path)
    paragraph = f"{NEW_MARK} Day 1, with a note.\nReworded on day 9."
    reworded = exempt(paragraph)
    page = root / "pinned" / "prereg.md"
    page.write_text(
        PREREG.replace("**Who wrote this and when.** Written on day 1.", paragraph),
        encoding="utf-8",
    )
    assert changed_files(root, commit, ("pinned",), reworded) == []
    # Without the exemption the same edit is a change.
    assert changed_files(root, commit, ("pinned",), {}) == ["pinned/prereg.md"]
    # A changed definition fails, whatever happens to the paragraph.
    page.write_text(PREREG.replace("Rule 1:", "Rule 2:"), encoding="utf-8")
    assert changed_files(root, commit, ("pinned",), reworded) == ["pinned/prereg.md"]
    # So does a missing paragraph.
    page.write_text(
        PREREG.replace("**Who wrote this and when.** Written on day 1.\n\n", ""), encoding="utf-8"
    )
    assert changed_files(root, commit, ("pinned",), reworded) == ["pinned/prereg.md"]


def test_the_command_says_when_only_the_paragraph_differs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, commit = prereg_repo(tmp_path)
    git(root, "tag", TAG)
    (root / "pinned" / "prereg.md").write_text(
        PREREG.replace("**Who wrote this and when.** Written on day 1.", f"{NEW_MARK} Day 1."),
        encoding="utf-8",
    )
    pin = (Pin(commit=commit, paths=("pinned",), tag=TAG),)
    assert main(["--root", str(root)], pins=pin, reworded=exempt(f"{NEW_MARK} Day 1.")) == 0
    out = capsys.readouterr().out
    assert "pinned/prereg.md" in out and "first paragraph" in out and "unchanged" in out


def test_only_the_pre_registrations_first_paragraph_may_be_reworded_to_its_pinned_text() -> None:
    (path,) = REWORDED
    assert path == "eval/PREREGISTRATION.md" and path in PINNED
    old_lead, new_lead, digest = REWORDED[path]
    assert (old_lead, new_lead) == ("**Who wrote this and when.**", "**When this was written.**")
    text = (Path(__file__).resolve().parents[1] / path).read_text(encoding="utf-8")
    (paragraph,) = [p for p in text.split("\n\n") if p.startswith(new_lead)]
    assert hashlib.sha256(paragraph.encode()).hexdigest() == digest
    # #90 was merged on 2026-11-17 (15:05 -0500); the paragraph gives that date.
    assert "reworded on 2026-11-17" in paragraph and "2026-11-18" not in paragraph


def test_the_paragraph_may_take_its_new_lead_but_not_lose_it(tmp_path: Path) -> None:
    root, commit = prereg_repo(tmp_path)
    page = root / "pinned" / "prereg.md"
    reworded = exempt(f"{NEW_MARK} Day 1.")
    page.write_text(
        PREREG.replace("**Who wrote this and when.** Written on day 1.", f"{NEW_MARK} Day 1."),
        encoding="utf-8",
    )
    assert changed_files(root, commit, ("pinned",), reworded) == []
    # The old lead is not enough now, and neither is a paragraph with no lead.
    page.write_text(PREREG.replace("Written on day 1.", "Day 1, reworded."), encoding="utf-8")
    assert changed_files(root, commit, ("pinned",), reworded) == ["pinned/prereg.md"]
    page.write_text(
        PREREG.replace("**Who wrote this and when.** Written on day 1.", "Day 1."), encoding="utf-8"
    )
    assert changed_files(root, commit, ("pinned",), reworded) == ["pinned/prereg.md"]


def test_a_sentence_added_to_the_reworded_paragraph_fails(tmp_path: Path) -> None:
    root, commit = prereg_repo(tmp_path)
    page = root / "pinned" / "prereg.md"
    reworded = exempt(f"{NEW_MARK} Day 1.")
    page.write_text(
        PREREG.replace(
            "**Who wrote this and when.** Written on day 1.", f"{NEW_MARK} Day 1. And a new rule."
        ),
        encoding="utf-8",
    )
    assert changed_files(root, commit, ("pinned",), reworded) == ["pinned/prereg.md"]


def test_the_dates_of_the_reworded_paragraph_are_the_merge_day() -> None:
    root = Path(__file__).resolve().parents[1]
    measured = (root / "filingcheck/measured.py").read_text(encoding="utf-8")
    assert "reworded on 2026-11-17" in measured and "2026-11-18" not in measured
    log = (root / "docs/decisions.md").read_text(encoding="utf-8")
    assert "2026-11-18" not in log
