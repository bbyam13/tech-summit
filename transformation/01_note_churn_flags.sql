-- Materialized view: ai_classify over DISTINCT agent notes (deduped)
-- Classifies each unique note text into churn_signal/at_risk/healthy
-- and assigns a numeric score. Silver tables join back on note text.

CREATE OR REFRESH MATERIALIZED VIEW note_churn_flags
AS
SELECT
  agent_note_text,
  ai_classify(
    agent_note_text,
    ARRAY('churn_signal', 'at_risk', 'healthy')
  ) AS churn_label,
  CASE ai_classify(agent_note_text, ARRAY('churn_signal', 'at_risk', 'healthy'))
    WHEN 'churn_signal' THEN 1.0
    WHEN 'at_risk'      THEN 0.6
    ELSE 0.1
  END AS churn_signal_score
FROM (
  SELECT DISTINCT agent_note_text
  FROM read_files('/Volumes/${catalog}/${schema}/raw_data/risk_snapshots/')
  WHERE agent_note_text IS NOT NULL
);
