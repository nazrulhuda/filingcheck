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


class FakeSecClient:
    def __enter__(self) -> "FakeSecClient":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def get_json(self, url: str) -> dict[str, dict[str, object]]:
        return {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}}


def test_run_companies_writes_ciks_and_prints_the_sec_titles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from filingcheck.ingest import sec_client

    path = tmp_path / "companies.yaml"
    path.write_text(
        "companies:\n  - {ticker: AAPL, name: Apple Inc., sector: technology, fiscal_year_end: 9,"
        " revenue_rule: standard, financebench: true, aliases: [Apple]}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(sec_client, "SecClient", FakeSecClient)
    assert cli.run_companies(path) == 0
    out = capsys.readouterr().out
    assert "AAPL   0000320193  Apple Inc." in out
    assert "1 companies written" in out
    assert "'0000320193'" in path.read_text(encoding="utf-8")


def test_an_unknown_stage_is_an_error() -> None:
    with pytest.raises(SystemExit):
        cli.main(["nonsense"])
