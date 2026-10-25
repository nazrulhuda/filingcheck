from pathlib import Path

import pytest

from filingcheck.ingest import __main__ as cli


def test_companies_stage_updates_the_companies_file(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[Path] = []

    def fake_run(path: Path) -> int:
        calls.append(path)
        print("25 companies")
        return 0

    monkeypatch.setattr(cli, "run_companies", fake_run)
    assert cli.main(["companies"]) == 0
    assert calls == [cli.COMPANIES_FILE]
    assert "25 companies" in capsys.readouterr().out


def test_an_unknown_stage_is_an_error() -> None:
    with pytest.raises(SystemExit):
        cli.main(["nonsense"])
