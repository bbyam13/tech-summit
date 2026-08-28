-- Domain question: Which critical-risk subscribers on NODE-OHIO-14 have the highest CLV at risk?
-- Runs against synced UC table in Lakebase Postgres
SELECT subscriber_id, plan_type, tenure_months, monthly_arpu_usd,
       service_node_id, home_metro, churn_risk_score, churn_reason,
       open_ticket_count, has_open_outage, clv_at_risk_usd, risk_band,
       service_summary
FROM synced_subscriber_position
WHERE risk_band = 'critical'
  AND service_node_id = 'NODE-OHIO-14'
ORDER BY clv_at_risk_usd DESC
LIMIT 10;
