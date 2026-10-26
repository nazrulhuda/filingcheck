-- Each chunk's section boundary, and the other Items of the same filing that contain its text.
-- A repeated passage is stored once, under its first Item; also_in lists the others.

ALTER TABLE chunks
    ADD COLUMN boundary text NOT NULL DEFAULT 'exact' CHECK (boundary IN ('exact', 'approximate')),
    ADD COLUMN also_in  text[] NOT NULL DEFAULT '{}';
