"""`make retrieval-eval` end to end: main() against Postgres, with fake embeddings and a
temporary root (integration)."""

import hashlib
import json
import shutil
from pathlib import Path

import psycopg
import pytest

from filingcheck.embeddings.fake import FakeEmbeddings
from filingcheck.eval import retrieval_report
from filingcheck.paths import REPO_ROOT
from tests.db.test_load import FILING
from tests.db.test_retrieval_db import (  # noqa: F401  (`searchable` is a fixture)
    AAPL_2024,
    IBM_2025,
    TOPICS,
    searchable,
)

pytestmark = pytest.mark.integration

QUESTIONS = [
    {
        "id": "ret-001",
        "source": "hand",
        "question": "Why did iPhone net sales go up, and in which regions?",
        "ticker": "AAPL",
        "fiscal_year": FILING.fiscal_year,
        "item": "7",
        "accession": FILING.accession,
        "chunk_index": 0,
        "must_contain": TOPICS[0][:30],
    },
    {
        "id": "ret-002",
        "source": "hand",
        "question": "How did the services business grow in fiscal 2024?",
        "ticker": "AAPL",
        "fiscal_year": AAPL_2024.fiscal_year,
        "item": "7",
        "accession": AAPL_2024.accession,
        "chunk_index": 1,
        "must_contain": TOPICS[1][:30],
    },
    {
        "id": "ret-003",
        "source": "hand",
        "question": "What does IBM say about software, consulting and hybrid cloud revenue?",
        "ticker": "IBM",
        "fiscal_year": IBM_2025.fiscal_year,
        "item": "7",
        "accession": IBM_2025.accession,
        "chunk_index": 0,
        "must_contain": "IBM software and consulting revenue",
    },
]


class NoEmbeddings(FakeEmbeddings):
    """Fails if asked to embed anything: the second run must reuse the saved vectors."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise AssertionError(f"asked to embed {len(texts)} texts")


@pytest.fixture
def root(tmp_path: Path) -> Path:
    (tmp_path / "data").mkdir()
    shutil.copy(REPO_ROOT / "data" / "companies.yaml", tmp_path / "data" / "companies.yaml")
    questions = tmp_path / "eval" / "questions" / "retrieval.jsonl"
    questions.parent.mkdir(parents=True)
    questions.write_text("".join(json.dumps(q) + "\n" for q in QUESTIONS), encoding="utf-8")
    (tmp_path / "docs").mkdir()
    return tmp_path


def test_the_report_is_written_then_rerun_from_the_saved_query_vectors(
    searchable: psycopg.Connection,  # noqa: F811
    fresh_db_url: str,
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", fresh_db_url)
    monkeypatch.setattr("filingcheck.embeddings.openai_client.OpenAIEmbeddings", FakeEmbeddings)
    assert retrieval_report.main(root) == 0

    report = (root / "docs" / "retrieval_report.md").read_text(encoding="utf-8")
    for retriever in ("vector", "keyword", "hybrid"):
        for name in ("none", "company + year"):
            assert f"| {retriever} | {name} |" in report
    assert "and saved to eval/results/retrieval_queries.parquet" in report
    assert "- embedding model: fake-embeddings" in report
    vectors = root / "eval" / "results" / "retrieval_queries.parquet"
    saved = hashlib.sha256(vectors.read_bytes()).hexdigest()

    monkeypatch.setattr("filingcheck.embeddings.openai_client.OpenAIEmbeddings", NoEmbeddings)
    assert retrieval_report.main(root) == 0
    rerun = (root / "docs" / "retrieval_report.md").read_text(encoding="utf-8")
    assert "loaded from eval/results/retrieval_queries.parquet" in rerun
    assert "this run reused them and made no API call" in rerun
    assert hashlib.sha256(vectors.read_bytes()).hexdigest() == saved
    # Same vectors, same database: the same scores; only the latency may differ.
    assert scores(rerun) == scores(report) and len(scores(report)) == 6


def scores(report: str) -> list[list[str]]:
    """Each score-table row up to the latency column."""
    rows = [
        line.split("|")
        for line in report.splitlines()
        if line.startswith(("| vector |", "| keyword |", "| hybrid |"))
    ]
    return [row[:9] for row in rows]
