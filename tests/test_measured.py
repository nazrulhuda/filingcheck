"""The measured system is pinned: `make verify-measured` fails on a change under a pinned path."""

import subprocess
from pathlib import Path

import pytest

from filingcheck.measured import PINNED, TAG, changed_files, main


def repo(tmp_path: Path) -> Path:
    """A repository with a pinned folder and a free one, tagged like the measured commit."""

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "test")
    (tmp_path / "pinned").mkdir()
    (tmp_path / "free").mkdir()
    (tmp_path / "pinned" / "rules.py").write_text("RULE = 1\n", encoding="utf-8")
    (tmp_path / "pinned" / "gold.jsonl").write_text('{"id": "q-1"}\n', encoding="utf-8")
    (tmp_path / "free" / "report.py").write_text("PAGE = 1\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-q", "-m", "the measured system")
    git("tag", TAG)
    return tmp_path


def test_nothing_changed_passes(tmp_path: Path) -> None:
    root = repo(tmp_path)
    assert changed_files(root, pinned=("pinned",)) == []


def test_a_changed_pinned_file_is_named_and_a_changed_free_file_is_not(tmp_path: Path) -> None:
    root = repo(tmp_path)
    (root / "free" / "report.py").write_text("PAGE = 2\n", encoding="utf-8")
    assert changed_files(root, pinned=("pinned",)) == []
    (root / "pinned" / "rules.py").write_text("RULE = 2\n", encoding="utf-8")
    assert changed_files(root, pinned=("pinned",)) == ["pinned/rules.py"]


def test_a_new_file_under_a_pinned_path_counts_as_a_change(tmp_path: Path) -> None:
    root = repo(tmp_path)
    (root / "pinned" / "extra.py").write_text("NEW = 1\n", encoding="utf-8")
    assert changed_files(root, pinned=("pinned",)) == ["pinned/extra.py"]


def test_a_single_pinned_file_is_pinned_on_its_own(tmp_path: Path) -> None:
    root = repo(tmp_path)
    (root / "pinned" / "gold.jsonl").write_text('{"id": "q-2"}\n', encoding="utf-8")
    assert changed_files(root, pinned=("pinned/rules.py",)) == []
    assert changed_files(root, pinned=("pinned/gold.jsonl",)) == ["pinned/gold.jsonl"]


def test_the_command_fails_and_names_the_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = repo(tmp_path)
    assert main(["--root", str(root), "--pinned", "pinned"]) == 0
    assert TAG in capsys.readouterr().out
    (root / "pinned" / "rules.py").write_text("RULE = 3\n", encoding="utf-8")
    assert main(["--root", str(root), "--pinned", "pinned"]) == 1
    out = capsys.readouterr().out
    assert "pinned/rules.py" in out and TAG in out


def test_the_pinned_list_is_the_plans_list() -> None:
    """The answering code, the grading and scoring code, the data pins and the measured sets."""
    assert TAG == "week6-measured"
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
    assert all((Path(__file__).resolve().parents[1] / p).exists() for p in PINNED)
