"""`make embed`: plan, then embed every chunk without a vector, saving after each batch.

A vector is paid for once. Before calling the API the run restores what is already known:
the disk mirror (`data/embeddings/<model>.parquet`) refills `embedding_cache`, and the cache
fills chunks by content hash. Only texts in neither are sent, and each distinct text once.
"""

import os
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import psycopg

from filingcheck.db.load import current_model, restore_embeddings
from filingcheck.embeddings import (
    MAX_BATCH_TEXTS,
    MAX_BATCH_TOKENS,
    EmbeddingClient,
    estimate_tokens,
    make_batches,
)
from filingcheck.llm.pricing import cost_usd, price_per_million

PROGRESS_EVERY = 1_000
HNSW_INDEX = (
    "CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw ON chunks "
    "USING hnsw (embedding halfvec_cosine_ops) WITH (m = 16, ef_construction = 64)"
)


class ModelMismatchError(RuntimeError):
    """The database holds vectors from another model; mixing models is refused."""


@dataclass(frozen=True)
class Plan:
    """What a run would do, computed without writing anything or calling the API."""

    model: str
    total_chunks: int
    missing_chunks: int  # chunks without an embedding
    covered_by_cache: int  # of those, chunks whose text is in the cache or the disk mirror
    chunks_to_embed: int
    texts_to_embed: int  # distinct texts sent to the API
    estimated_tokens: int
    estimated_cost_usd: float


@dataclass(frozen=True)
class Result:
    """What a run did."""

    restored: int  # chunks filled from the cache or the mirror
    embedded: int  # distinct texts sent to the API
    tokens: int
    cost_usd: float
    index_created: bool


def mirror_path(root: Path, model: str) -> Path:
    """Where the vectors of `model` are mirrored on disk (git-ignored)."""
    return root / "data" / "embeddings" / f"{model}.parquet"


def check_model(conn: psycopg.Connection, client: EmbeddingClient) -> None:
    """Refuse to embed with a model other than the one already recorded."""
    row = conn.execute(
        "SELECT model, dimensions FROM embeddings_meta ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if row and (row[0], row[1]) != (client.model_name, client.dimensions):
        raise ModelMismatchError(
            f"the database holds {row[0]} vectors ({row[1]} dimensions); refusing to add "
            f"{client.model_name} vectors. Mixing models makes search scores meaningless."
        )


def plan(conn: psycopg.Connection, client: EmbeddingClient, mirror: Path) -> Plan:
    """Count what a run would restore and embed; reads only, no API call."""
    check_model(conn, client)
    total, missing = conn.execute(
        "SELECT count(*), count(*) FILTER (WHERE embedding IS NULL) FROM chunks"
    ).fetchone() or (0, 0)
    cached = {
        row[0]
        for row in conn.execute(
            "SELECT content_hash FROM embedding_cache WHERE model = %s", (client.model_name,)
        )
    } | _mirror_hashes(mirror)
    pending = conn.execute(
        "SELECT content_hash, text FROM chunks WHERE embedding IS NULL"
    ).fetchall()
    covered = sum(1 for h, _ in pending if h in cached)
    texts = {h: t for h, t in pending if h not in cached}
    tokens = sum(estimate_tokens(t) for t in texts.values())
    return Plan(
        model=client.model_name,
        total_chunks=int(total),
        missing_chunks=int(missing),
        covered_by_cache=covered,
        chunks_to_embed=len(pending) - covered,
        texts_to_embed=len(texts),
        estimated_tokens=tokens,
        estimated_cost_usd=cost_usd(client.model_name, tokens),
    )


def describe(p: Plan) -> str:
    """The plan as printed before a run."""
    price = price_per_million(p.model)
    return "\n".join(
        [
            f"model: {p.model}",
            f"chunks: {p.total_chunks:,}; without an embedding: {p.missing_chunks:,}",
            f"covered by the cache or the disk mirror: {p.covered_by_cache:,} chunks (free)",
            f"to embed through the API: {p.chunks_to_embed:,} chunks, "
            f"{p.texts_to_embed:,} distinct texts",
            f"estimated tokens: {p.estimated_tokens:,} (characters / 3, an upper estimate)",
            f"estimated cost: ${p.estimated_cost_usd:.4f} at ${price} per million tokens",
        ]
    )


def run(
    conn: psycopg.Connection,
    client: EmbeddingClient,
    mirror: Path,
    *,
    workers: int = 4,
    max_texts: int = MAX_BATCH_TEXTS,
    max_tokens: int = MAX_BATCH_TOKENS,
    log: Callable[[str], None] = print,
) -> Result:
    """Restore what is cached, embed the rest batch by batch, then mirror and index.

    Each batch is saved to `embedding_cache` and `chunks` as soon as it returns, so a crash
    loses only the batches still in flight; a second run resumes where this one stopped.
    """
    check_model(conn, client)
    with conn.transaction():
        if current_model(conn) is None:
            conn.execute(
                "INSERT INTO embeddings_meta (model, dimensions) VALUES (%s, %s)",
                (client.model_name, client.dimensions),
            )
        _import_mirror(conn, client.model_name, mirror)
        restored = restore_embeddings(conn, client.model_name)
    pending: dict[str, str] = dict(
        conn.execute(
            "SELECT DISTINCT ON (content_hash) content_hash, text FROM chunks "
            "WHERE embedding IS NULL ORDER BY content_hash"
        ).fetchall()
    )
    conn.commit()
    by_text = {text: h for h, text in pending.items()}
    batches = make_batches(list(pending.values()), max_texts, max_tokens)
    embedded = 0
    first_error: BaseException | None = None
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures: dict[Future[list[list[float]]], list[str]] = {
            pool.submit(client.embed, batch): batch for batch in batches
        }
        for future in as_completed(futures):
            try:
                vectors = future.result()
            except Exception as exc:  # keep saving the batches that did come back
                if first_error is None:
                    first_error = exc
                    for other in futures:
                        other.cancel()
                continue
            batch = futures[future]
            _save(
                conn,
                client.model_name,
                [(by_text[t], v) for t, v in zip(batch, vectors, strict=True)],
            )
            before = embedded
            embedded += len(batch)
            if embedded // PROGRESS_EVERY > before // PROGRESS_EVERY:
                log(f"embedded {embedded:,} of {len(pending):,} texts")
    _write_mirror(conn, client.model_name, mirror)
    if first_error is not None:
        raise first_error
    index_created = _index_if_complete(conn)
    return Result(
        restored=restored,
        embedded=embedded,
        tokens=client.tokens_used,
        cost_usd=cost_usd(client.model_name, client.tokens_used),
        index_created=index_created,
    )


def _vector_text(vector: list[float]) -> str:
    return "[" + ",".join(f"{x:.7g}" for x in vector) + "]"


def _save(conn: psycopg.Connection, model: str, rows: list[tuple[str, list[float]]]) -> None:
    with conn.transaction():
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO embedding_cache (model, content_hash, embedding) "
                "VALUES (%s, %s, %s::halfvec) ON CONFLICT DO NOTHING",
                [(model, h, _vector_text(v)) for h, v in rows],
            )
        conn.execute(
            "UPDATE chunks c SET embedding = e.embedding FROM embedding_cache e "
            "WHERE e.model = %s AND e.content_hash = c.content_hash "
            "AND c.content_hash = ANY(%s) AND c.embedding IS NULL",
            (model, [h for h, _ in rows]),
        )


def _mirror_hashes(mirror: Path) -> set[str]:
    if not mirror.exists():
        return set()
    import pyarrow.parquet as pq  # only `make embed` needs pyarrow

    return set(pq.read_table(mirror, columns=["content_hash"]).column(0).to_pylist())


def _import_mirror(conn: psycopg.Connection, model: str, mirror: Path) -> None:
    if not mirror.exists():
        return
    import pyarrow.parquet as pq

    table = pq.read_table(mirror)
    hashes = table.column("content_hash").to_pylist()
    vectors = table.column("vector").to_pylist()
    conn.execute(
        "CREATE TEMP TABLE mirror_import (content_hash text, embedding text) ON COMMIT DROP"
    )
    with conn.cursor() as cur, cur.copy("COPY mirror_import FROM STDIN") as copy:
        for h, v in zip(hashes, vectors, strict=True):
            copy.write_row((h, _vector_text(v)))
    conn.execute(
        "INSERT INTO embedding_cache (model, content_hash, embedding) "
        "SELECT %s, content_hash, embedding::halfvec FROM mirror_import "
        "ON CONFLICT DO NOTHING",
        (model,),
    )


def _write_mirror(conn: psycopg.Connection, model: str, mirror: Path) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    rows = conn.execute(
        "SELECT content_hash, embedding::text FROM embedding_cache WHERE model = %s "
        "ORDER BY content_hash",
        (model,),
    ).fetchall()
    conn.commit()
    table = pa.table(
        {
            "content_hash": pa.array([h for h, _ in rows], pa.string()),
            "vector": pa.array(
                [[float(x) for x in text.strip("[]").split(",")] for _, text in rows],
                pa.list_(pa.float32()),
            ),
        }
    )
    mirror.parent.mkdir(parents=True, exist_ok=True)
    tmp = mirror.with_name(mirror.name + ".tmp")
    pq.write_table(table, tmp)
    os.replace(tmp, mirror)


def _index_if_complete(conn: psycopg.Connection) -> bool:
    """Create the HNSW index once every chunk has a vector; True if it was created now."""
    row = conn.execute("SELECT count(*) FROM chunks WHERE embedding IS NULL").fetchone()
    if row and row[0]:
        conn.commit()
        return False
    exists = conn.execute(
        "SELECT 1 FROM pg_indexes WHERE indexname = 'chunks_embedding_hnsw'"
    ).fetchone()
    conn.execute(HNSW_INDEX)
    conn.execute("ANALYZE chunks")
    conn.commit()
    return exists is None
