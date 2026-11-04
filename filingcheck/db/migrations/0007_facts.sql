-- Numeric XBRL facts from each pinned filing's own inline XBRL (data/facts.jsonl), one row per
-- fact as filed: the value in its own unit with scale and sign applied, its period (a start
-- and end, or an instant), its dimensions (empty for company totals) and the attributes as
-- written. This replaces the companyfacts-shaped table of 0001, which was never loaded.
DROP TABLE facts;

CREATE TABLE facts (
    id           bigserial PRIMARY KEY,
    filing_id    bigint NOT NULL REFERENCES filings (id) ON DELETE CASCADE,
    concept      text NOT NULL,
    value        numeric NOT NULL,
    unit         text NOT NULL,
    period_start date,
    period_end   date,
    instant      date,
    decimals     text,
    scale        integer,
    sign         text,
    dimensions   jsonb NOT NULL DEFAULT '{}'::jsonb,
    context_ref  text NOT NULL,
    conflict     boolean NOT NULL DEFAULT false,
    CHECK ((instant IS NULL) <> (period_end IS NULL)),
    CHECK (period_start IS NULL OR period_end IS NOT NULL)
);
-- No unique index: the facts stage keeps each fact once (tested, and locked by
-- data/facts_snapshot.json), and such an index would take about 80 MB of Neon's 1 GB.

CREATE INDEX facts_filing_concept_idx ON facts (filing_id, concept);
CREATE INDEX facts_filing_concept_totals_idx ON facts (filing_id, concept)
    WHERE dimensions = '{}'::jsonb;
