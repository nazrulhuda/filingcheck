-- Number tables set aside from the prose, one row per table. companyfacts has whole-company
-- numbers only; segment numbers (product lines, business segments) exist only in these
-- tables. They have no embedding and no tsvector: the search over chunks does not see them.

CREATE TABLE table_chunks (
    id          bigserial PRIMARY KEY,
    filing_id   bigint NOT NULL REFERENCES filings (id) ON DELETE CASCADE,
    item        text,               -- NULL when the table is outside Items 1, 1A, 7, 7A and 8
    table_index integer NOT NULL,   -- order of the table in the filing
    source_url  text NOT NULL,      -- the 10-K or the Exhibit 13 that holds it
    position    integer NOT NULL,   -- character offset of the table in that document
    text        text NOT NULL,      -- one row per line, "label: value | value"
    UNIQUE (filing_id, table_index)
);
CREATE INDEX table_chunks_filing_item_idx ON table_chunks (filing_id, item);
