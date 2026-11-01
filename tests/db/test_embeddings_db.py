"""The embedding cache, migration 0004, the loader's restore, and the embed run (integration)."""

from pathlib import Path

import psycopg
import pytest

from filingcheck.db.load import load_all
from filingcheck.db.migrate import migrate, migration_files, render
from filingcheck.embeddings import content_hash
from filingcheck.embeddings.fake import FakeEmbeddings
from filingcheck.embeddings.runner import ModelMismatchError, plan, run
from filingcheck.ingest.chunking import Chunk
from filingcheck.ingest.filings import Manifest
from tests.db.test_load import APPLE, FILING, chunks, write_jsonl

pytestmark = pytest.mark.integration


def loaded(db: psycopg.Connection, tmp_path: Path, rows: list[Chunk] | None = None) -> Path:
    migrate(db)
    path = write_jsonl(tmp_path / "chunks.jsonl", rows if rows is not None else chunks(40))
    load_all(db, [APPLE], Manifest(filings=[FILING]), path)
    return path


def count(db: psycopg.Connection, sql: str) -> int:
    row = db.execute(sql).fetchone()
    return int(row[0]) if row else 0


# ---------------------------------------------------------------- migration and loader


def test_the_migration_backfills_the_same_hash_python_computes(
    db: psycopg.Connection,
) -> None:
    for path in migration_files()[:3]:  # the schema before 0004, with chunks already loaded
        db.execute(render(path.read_text(encoding="utf-8")).encode())
    db.execute(
        "INSERT INTO companies (ticker, cik, name, sector, fiscal_year_end, revenue_rule)"
        " VALUES ('AAPL', '0000320193', 'Apple', 'tech', 9, 'standard')"
    )
    db.execute(
        "INSERT INTO filings (ticker, cik, accession, form, filing_date, period_of_report,"
        " fiscal_year, primary_url) VALUES ('AAPL', '0000320193', 'a', '10-K',"
        " '2025-10-31', '2025-09-27', 2025, 'u')"
    )
    texts = ["Net sales rose 6%.", "Résumé of risks — “quoted” €"]
    for i, text in enumerate(texts):
        db.execute(
            "INSERT INTO chunks (filing_id, item, chunk_index, char_start, char_end, text)"
            " VALUES (1, '7', %s, 0, 1, %s)",
            (i, text),
        )
    db.execute(render(migration_files()[3].read_text(encoding="utf-8")).encode())
    hashes = [r[0] for r in db.execute("SELECT content_hash FROM chunks ORDER BY chunk_index")]
    assert hashes == [content_hash(t) for t in texts]


def test_the_loader_stores_each_chunks_content_hash(db: psycopg.Connection, tmp_path: Path) -> None:
    loaded(db, tmp_path)
    rows = db.execute(
        "SELECT content_hash, encode(sha256(convert_to(text, 'UTF8')), 'hex') FROM chunks"
    ).fetchall()
    assert rows and all(stored == computed for stored, computed in rows)


def test_the_loader_restores_embeddings_from_the_cache_by_hash(
    db: psycopg.Connection, tmp_path: Path
) -> None:
    path = loaded(db, tmp_path)
    run(db, FakeEmbeddings(), tmp_path / "mirror.parquet", log=lambda m: None)
    before = db.execute("SELECT content_hash, embedding::text FROM chunks ORDER BY id").fetchall()
    counts = load_all(db, [APPLE], Manifest(filings=[FILING]), path)  # replaces every chunk
    after = db.execute("SELECT content_hash, embedding::text FROM chunks ORDER BY id").fetchall()
    assert counts["embeddings_restored"] == 40
    assert after == before


# ---------------------------------------------------------------- the embed run


def test_a_dry_run_plan_makes_no_api_calls_and_counts_right(
    db: psycopg.Connection, tmp_path: Path
) -> None:
    rows = chunks(40)
    rows.append(rows[0].model_copy(update={"chunk_index": 99}))  # a repeated text, embedded once
    loaded(db, tmp_path, rows)
    fake = FakeEmbeddings()
    p = plan(db, fake, tmp_path / "mirror.parquet")
    assert (p.missing_chunks, p.covered_by_cache, p.texts_to_embed) == (41, 0, 40)
    assert p.estimated_tokens == sum(max(1, len(c.text) // 3) for c in rows[:40])
    assert fake.calls == 0
    assert count(db, "SELECT count(*) FROM embedding_cache") == 0
    assert count(db, "SELECT count(*) FROM embeddings_meta") == 0


def test_a_run_embeds_everything_once_and_a_second_run_has_nothing_to_do(
    db: psycopg.Connection, tmp_path: Path
) -> None:
    loaded(db, tmp_path)
    fake = FakeEmbeddings()
    result = run(db, fake, tmp_path / "mirror.parquet", log=lambda m: None)
    assert result.embedded == 40 and result.index_created
    assert count(db, "SELECT count(*) FROM chunks WHERE embedding IS NULL") == 0
    assert count(db, "SELECT count(*) FROM embeddings_meta") == 1
    assert (
        count(db, "SELECT count(*) FROM pg_indexes WHERE indexname = 'chunks_embedding_hnsw'") == 1
    )
    assert plan(db, FakeEmbeddings(), tmp_path / "mirror.parquet").texts_to_embed == 0


def test_a_cache_hit_skips_the_api(db: psycopg.Connection, tmp_path: Path) -> None:
    loaded(db, tmp_path)
    run(db, FakeEmbeddings(), tmp_path / "mirror.parquet", log=lambda m: None)
    db.execute("UPDATE chunks SET embedding = NULL")
    db.commit()
    again = FakeEmbeddings()
    result = run(db, again, tmp_path / "mirror.parquet", log=lambda m: None)
    assert again.calls == 0 and result.embedded == 0 and result.restored == 40
    assert count(db, "SELECT count(*) FROM chunks WHERE embedding IS NULL") == 0


def test_the_disk_mirror_refills_an_empty_cache(db: psycopg.Connection, tmp_path: Path) -> None:
    mirror = tmp_path / "mirror.parquet"
    loaded(db, tmp_path)
    run(db, FakeEmbeddings(), mirror, log=lambda m: None)
    assert mirror.exists()
    db.execute("TRUNCATE embedding_cache, embeddings_meta")  # as after `make db-reset`
    db.execute("UPDATE chunks SET embedding = NULL")
    db.commit()
    fresh = FakeEmbeddings()
    assert plan(db, fresh, mirror).covered_by_cache == 40
    result = run(db, fresh, mirror, log=lambda m: None)
    assert fresh.calls == 0 and result.embedded == 0
    assert count(db, "SELECT count(*) FROM chunks WHERE embedding IS NULL") == 0


def test_a_crashed_run_resumes_without_re_embedding_what_was_saved(
    db: psycopg.Connection, tmp_path: Path
) -> None:
    loaded(db, tmp_path)
    failing = FakeEmbeddings(fail_after_calls=2)
    with pytest.raises(RuntimeError, match="fake failure"):
        run(db, failing, tmp_path / "m.parquet", max_texts=10, workers=1, log=lambda m: None)
    assert count(db, "SELECT count(*) FROM embedding_cache") == 20  # two batches were saved
    second = FakeEmbeddings()
    result = run(db, second, tmp_path / "m.parquet", max_texts=10, workers=1, log=lambda m: None)
    assert result.embedded == 20 and second.calls == 2
    assert count(db, "SELECT count(*) FROM chunks WHERE embedding IS NULL") == 0


def test_mixing_models_is_refused(db: psycopg.Connection, tmp_path: Path) -> None:
    loaded(db, tmp_path)
    run(db, FakeEmbeddings(model_name="model-a"), tmp_path / "a.parquet", log=lambda m: None)
    other = FakeEmbeddings(model_name="model-b")
    with pytest.raises(ModelMismatchError, match="model-a"):
        plan(db, other, tmp_path / "b.parquet")
    with pytest.raises(ModelMismatchError, match="model-a"):
        run(db, other, tmp_path / "b.parquet", log=lambda m: None)
    assert other.calls == 0
