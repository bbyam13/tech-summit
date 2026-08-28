-- Agentic Schema Migration
-- Co-authored-by: Genie Code <genie-code@databricks.com>
-- Branch: dev-retention-schema
-- Purpose: Add ML-driven priority scoring for retention agent workflow

-- Migration 1: Add priority_score column
ALTER TABLE retention_actions
ADD COLUMN IF NOT EXISTS priority_score NUMERIC(5,2)
    DEFAULT 0.0
    CHECK (priority_score >= 0 AND priority_score <= 100);

-- Migration 2: Composite index for retention agent access pattern
CREATE INDEX IF NOT EXISTS idx_retention_actions_subscriber_outcome
ON retention_actions (subscriber_id, outcome, created_at DESC);

-- Migration 3: Backfill priority scores
UPDATE retention_actions
SET priority_score = CASE
    WHEN outcome = 'pending' THEN 80.0
    WHEN outcome = 'escalated' THEN 95.0
    WHEN outcome = 'retained' THEN 10.0
    ELSE 50.0
END;
