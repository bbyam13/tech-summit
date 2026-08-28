-- Gold: one row per subscriber — current position
-- The coherence spine: dashboard, metric view, Genie, app all read this.
-- Built from silver_risk (current snapshot) + silver_tickets + silver_billing.

CREATE OR REFRESH MATERIALIZED VIEW gold_subscriber_position
AS
WITH current_risk AS (
  SELECT *
  FROM silver_risk
  WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM silver_risk)
)
SELECT
  cr.subscriber_id,
  cr.plan_type,
  cr.tenure_months,
  cr.monthly_arpu_usd,
  cr.service_node_id,
  cr.home_metro,
  cr.state,
  cr.sub_lat,
  cr.sub_lng,
  cr.service_summary,
  cr.churn_risk_score,
  cr.churn_reason,
  COALESCE(st.open_ticket_count, 0) AS open_ticket_count,
  COALESCE(st.has_open_outage, FALSE) AS has_open_outage,
  COALESCE(st.has_open_billing, FALSE) AS has_open_billing,
  COALESCE(sb.has_recent_dispute, FALSE) AS has_recent_dispute,
  cr.churn_signal_score,
  -- CLV at risk: monthly_arpu * 24 * churn_risk when risk >= 0.6, else 0
  CASE
    WHEN cr.churn_risk_score >= 0.6
    THEN ROUND(cr.monthly_arpu_usd * 24 * cr.churn_risk_score, 2)
    ELSE 0.0
  END AS clv_at_risk_usd,
  -- risk_band: critical (>=0.75 + open ticket), elevated (>=0.6), watch (>=0.4), healthy
  CASE
    WHEN cr.churn_risk_score >= 0.75 AND COALESCE(st.open_ticket_count, 0) > 0 THEN 'critical'
    WHEN cr.churn_risk_score >= 0.6 THEN 'elevated'
    WHEN cr.churn_risk_score >= 0.4 THEN 'watch'
    ELSE 'healthy'
  END AS risk_band
FROM current_risk cr
LEFT JOIN silver_tickets st ON cr.subscriber_id = st.subscriber_id
LEFT JOIN silver_billing sb ON cr.subscriber_id = sb.subscriber_id;
