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


class FakeFilingsClient:
    """A stand-in for SecClient that serves the canned responses of test_filings."""

    def __init__(self) -> None:
        from tests.ingest.test_filings import FakeClient, documents, submissions

        data = documents(submissions(), {"k25.htm": 2025, "k24.htm": 2024, "k23.htm": 2023})
        self.inner = FakeClient(data)
        self.downloads = 0

    def __enter__(self) -> "FakeFilingsClient":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def get_json(self, url: str) -> object:
        return self.inner.get_json(url)

    def get_bytes(self, url: str) -> bytes:
        self.downloads += 1
        return self.inner.get_bytes(url)


def test_run_filings_pins_filings_then_reuses_the_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from filingcheck.ingest import sec_client

    companies = tmp_path / "companies.yaml"
    companies.write_text(
        "companies:\n  - {ticker: AAPL, name: Apple Inc., cik: '0000320193', sector: technology,"
        " fiscal_year_end: 9, revenue_rule: standard, financebench: true, aliases: [Apple]}\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "manifest.json"
    monkeypatch.setattr(sec_client, "SecClient", FakeFilingsClient)

    assert cli.run_filings(companies, manifest, tmp_path) == 0
    first = capsys.readouterr().out
    assert "chose 3 filings" in first
    assert "AAPL   2023, 2024, 2025" in first

    assert cli.run_filings(companies, manifest, tmp_path) == 0
    second = capsys.readouterr().out
    assert "using the filings pinned in manifest.json; 0 documents saved" in second
    assert "0 downloaded from sec.gov" in second


def test_the_filings_stage_passes_the_reselect_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[bool] = []

    def fake_run(companies: Path, manifest: Path, root: Path, reselect: bool = False) -> int:
        seen.append(reselect)
        return 0

    monkeypatch.setattr(cli, "run_filings", fake_run)
    assert cli.main(["filings"]) == 0
    assert cli.main(["filings", "--reselect"]) == 0
    assert seen == [False, True]


class FakeSectionsClient:
    """A stand-in for SecClient whose filing index lists no Exhibit 13."""

    def __init__(self) -> None:
        self.downloads = 0

    def __enter__(self) -> "FakeSectionsClient":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def get_bytes(self, url: str) -> bytes:
        fixtures = Path(__file__).resolve().parents[1] / "fixtures"
        index = (fixtures / "filing_index_sample.html").read_text(encoding="utf-8")
        return index.replace("EX-13", "EX-99").encode()


def test_run_sections_then_run_chunks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import json

    from filingcheck.ingest import sec_client
    from filingcheck.ingest.filings import Manifest, write_manifest
    from tests.ingest.test_sections import filing, fixture, write_document

    path = write_document(tmp_path, fixture("tenk_sample.html"))
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, Manifest(filings=[filing(path)]))
    monkeypatch.setattr(sec_client, "SecClient", FakeSectionsClient)

    assert cli.run_sections(manifest, tmp_path) == 0
    out = capsys.readouterr().out
    assert "5 Items saved from 1 filings" in out
    assert "GAP: Items 7 and 8 are short and the filing has no Exhibit 13" in out  # tiny sample
    assert (tmp_path / cli.SECTIONS_SUMMARY).exists()

    assert cli.run_chunks(manifest, tmp_path) == 0
    out = capsys.readouterr().out
    assert "chunks written" in out
    lines = (tmp_path / cli.CHUNKS_FILE).read_text(encoding="utf-8").splitlines()
    assert lines and {json.loads(line)["ticker"] for line in lines} == {"EXMP"}


def test_the_sections_and_chunks_stages_are_wired(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_sections(manifest: Path, root: Path) -> int:
        calls.append("s")
        return 0

    def fake_chunks(manifest: Path, root: Path) -> int:
        calls.append("c")
        return 0

    monkeypatch.setattr(cli, "run_sections", fake_sections)
    monkeypatch.setattr(cli, "run_chunks", fake_chunks)
    assert cli.main(["sections"]) == 0
    assert cli.main(["chunks"]) == 0
    assert calls == ["s", "c"]
