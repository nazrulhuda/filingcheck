"""The load command refuses to run without the facts file (no database needed)."""

from pathlib import Path

import pytest

from filingcheck.ingest import __main__ as cli


def no_database(*args: object, **kwargs: object) -> None:
    raise AssertionError("the load connected to the database")


@pytest.mark.parametrize("only", [None, "facts"])
def test_a_load_without_the_facts_file_fails_before_touching_the_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    only: str | None,
) -> None:
    import filingcheck.db

    monkeypatch.setattr(filingcheck.db, "connect", no_database)
    (tmp_path / "data").mkdir()
    (tmp_path / cli.CHUNKS_FILE).write_text("", encoding="utf-8")
    code = cli.run_load(tmp_path / "companies.yaml", tmp_path / "manifest.json", tmp_path, only)
    assert code == 1
    out = capsys.readouterr().out
    assert "data/facts.jsonl" in out and "make ingest" in out
