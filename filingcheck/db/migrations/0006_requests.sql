-- The API's request log: one row per /ask or /ask/stream call that passed the per-address
-- limit. `error` holds only a short code (provider, HTTP status, the provider's error code,
-- or "refused:daily_cap"), never a provider's message. Addresses are stored as keyed hashes.
CREATE TABLE requests (
    id                uuid PRIMARY KEY,
    created_at        timestamptz NOT NULL DEFAULT now(),
    question_hash     text NOT NULL,
    question          text NOT NULL,
    ticker            text,
    fiscal_year       integer,
    model_used        text,
    retriever         text,
    degraded          boolean NOT NULL DEFAULT false,
    latency_ms        double precision,
    prompt_tokens     integer,
    completion_tokens integer,
    cost_usd          double precision,
    abstained         boolean,
    error             text,
    client_ip_hash    text NOT NULL
);
CREATE INDEX requests_created_at ON requests (created_at);
CREATE INDEX requests_client_created ON requests (client_ip_hash, created_at);

-- Answers to the example questions, filled by `make examples` and served by /examples,
-- with the company and fiscal year each question was asked with.
CREATE TABLE example_answers (
    id          serial PRIMARY KEY,
    question    text NOT NULL UNIQUE,
    ticker      text,
    fiscal_year integer,
    answer_json jsonb NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);
