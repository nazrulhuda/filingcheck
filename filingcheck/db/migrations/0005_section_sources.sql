-- Where each saved section's text really lives, so a citation links to the right document.
-- IBM's Items 7 and 8 come from its Exhibit 13, not from the 10-K itself; for those the
-- source is the exhibit's URL, for every other section the 10-K's primary document.

CREATE TABLE section_sources (
    filing_id  bigint NOT NULL REFERENCES filings (id) ON DELETE CASCADE,
    item       text NOT NULL,
    method     text NOT NULL,
    source_url text NOT NULL,
    PRIMARY KEY (filing_id, item)
);
