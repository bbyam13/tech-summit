-- Silver: current + recent risk position
-- Joins risk_snapshots with subscribers and note_churn_flags

CREATE OR REFRESH MATERIALIZED VIEW silver_risk
CLUSTER BY (snapshot_date)
AS
SELECT
  r.subscriber_id,
  r.snapshot_date,
  r.churn_risk_score,
  r.churn_reason,
  r.open_ticket_count,
  r.agent_note_text,
  COALESCE(ncf.churn_signal_score, 0.1) AS churn_signal_score,
  s.plan_type,
  s.tenure_months,
  s.monthly_arpu_usd,
  s.service_node_id,
  s.home_metro,
  s.state,
  s.sub_lat,
  s.sub_lng,
  s.service_summary,
  s.activation_date,
  s.is_active
FROM read_files('/Volumes/${catalog}/${schema}/raw_data/risk_snapshots/') r
JOIN read_files('/Volumes/${catalog}/${schema}/raw_data/subscribers/') s
  ON r.subscriber_id = s.subscriber_id
LEFT JOIN note_churn_flags ncf
  ON r.agent_note_text = ncf.agent_note_text;
