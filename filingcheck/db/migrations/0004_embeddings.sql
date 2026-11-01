-- Paid vectors are cached by (model, content hash), so reloading the chunks never throws them
-- away. content_hash is the SHA-256 hex digest of the chunk text as UTF-8; the loader
-- computes the same value in Python. The table already has rows, so the column is added
-- nullable, filled in, then made NOT NULL.

ALTER TABLE chunks ADD COLUMN content_hash text;
UPDATE chunks SET content_hash = encode(sha256(convert_to(text, 'UTF8')), 'hex');
ALTER TABLE chunks ALTER COLUMN content_hash SET NOT NULL;
CREATE INDEX chunks_content_hash_idx ON chunks (content_hash);

CREATE TABLE embedding_cache (
    model        text NOT NULL,
    content_hash text NOT NULL,
    embedding    halfvec({{EMBEDDING_DIMENSIONS}}) NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (model, content_hash)
);
