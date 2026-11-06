-- The request log records whether the agent's checks ran (NULL for the baseline and for rows
-- written before this migration) and, for the agent, the override log: one record per check
-- per checked tool call, with the value the model sent, the value used and the reason.
ALTER TABLE requests ADD COLUMN checks boolean;
ALTER TABLE requests ADD COLUMN overrides jsonb;
