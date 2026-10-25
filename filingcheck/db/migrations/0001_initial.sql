-- The initial schema. {{EMBEDDING_DIMENSIONS}} is filled in from filingcheck.db.EMBEDDING_DIMENSIONS.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE companies (
    ticker          text PRIMARY KEY,
    cik             text NOT NULL UNIQUE CHECK (cik ~ '^[0-9]{10}$'),
    name            text NOT NULL,
    sector          text NOT NULL,
    fiscal_year_end smallint NOT NULL CHECK (fiscal_year_end BETWEEN 1 AND 12),
    revenue_rule    text NOT NULL CHECK (revenue_rule IN ('standard', 'bank')),
    aliases         jsonb NOT NULL DEFAULT '[]'
);

CREATE TABLE filings (
    id               bigserial PRIMARY KEY,
    ticker           text NOT NULL REFERENCES companies (ticker),
    cik              text NOT NULL,
    accession        text NOT NULL UNIQUE,
    form             text NOT NULL,
    filing_date      date NOT NULL,
    period_of_report date NOT NULL,
    fiscal_year      integer NOT NULL,
    primary_url      text NOT NULL,
    UNIQUE (ticker, fiscal_year)
);

CREATE TABLE chunks (
    id          bigserial PRIMARY KEY,
    filing_id   bigint NOT NULL REFERENCES filings (id) ON DELETE CASCADE,
    item        text NOT NULL,
    chunk_index integer NOT NULL,
    char_start  integer NOT NULL,
    char_end    integer NOT NULL,
    text        text NOT NULL,
    tsv         tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
    embedding   halfvec({{EMBEDDING_DIMENSIONS}}),
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (filing_id, item, chunk_index)
);
CREATE INDEX chunks_tsv_idx ON chunks USING gin (tsv);
CREATE INDEX chunks_filing_item_idx ON chunks (filing_id, item);
-- The HNSW index on chunks.embedding is created once the embeddings exist.

-- Which model made the vectors in chunks.embedding. The live app embeds each question with
-- the same model, so question and chunk vectors are comparable.
CREATE TABLE embeddings_meta (
    id         serial PRIMARY KEY,
    model      text NOT NULL,
    dimensions integer NOT NULL CHECK (dimensions = {{EMBEDDING_DIMENSIONS}}),
    created_at timestamptz NOT NULL DEFAULT now()
);

-- XBRL facts from the SEC companyfacts files, stored as filed (raw value and unit).
-- Instant facts such as total assets have no start date, so NULLs must count as equal
-- for the uniqueness check.
CREATE TABLE facts (
    id         bigserial PRIMARY KEY,
    cik        text NOT NULL,
    taxonomy   text NOT NULL,
    tag        text NOT NULL,
    unit       text NOT NULL,
    value      numeric NOT NULL,
    start_date date,
    end_date   date NOT NULL,
    fy         integer,
    fp         text,
    form       text,
    filed      date,
    accession  text NOT NULL,
    frame      text,
    UNIQUE NULLS NOT DISTINCT (cik, taxonomy, tag, unit, end_date, start_date, accession)
);

CREATE TABLE eval_questions (
    id       text PRIMARY KEY,
    set_name text NOT NULL,
    category text NOT NULL,
    question text NOT NULL,
    details  jsonb NOT NULL DEFAULT '{}'
);

CREATE TABLE eval_runs (
    id         bigserial PRIMARY KEY,
    started_at timestamptz NOT NULL DEFAULT now(),
    model      text NOT NULL,
    config     jsonb NOT NULL DEFAULT '{}',
    notes      text
);

CREATE TABLE eval_answers (
    id          bigserial PRIMARY KEY,
    run_id      bigint NOT NULL REFERENCES eval_runs (id) ON DELETE CASCADE,
    question_id text NOT NULL REFERENCES eval_questions (id),
    answer      text,
    details     jsonb NOT NULL DEFAULT '{}',
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (run_id, question_id)
);
