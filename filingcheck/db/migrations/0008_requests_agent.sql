-- The request log records which answerer ran each question and, for the agent, its tool
-- calls and restarts. Rows written before this migration, and every baseline answer, have
-- mode 'baseline' and no tool calls.
ALTER TABLE requests ADD COLUMN mode text NOT NULL DEFAULT 'baseline'
    CHECK (mode IN ('baseline', 'agent'));
ALTER TABLE requests ADD COLUMN tool_calls jsonb;
