-- Each figure of the answer with its number label (Verified, Conflict or Unverified) and
-- where it was found, computed after the model finished. NULL where no answer was given and
-- for rows written before this migration.
ALTER TABLE requests ADD COLUMN number_labels jsonb;
