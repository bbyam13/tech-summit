-- Live view: at-risk subscribers ranked by CLV at risk
-- Reads from synced UC tables in Lakebase Postgres (production)
SELECT s.subscriber_id, s.plan_type, s.tenure_months, s.monthly_arpu_usd,
       s.service_node_id, s.home_metro, s.churn_risk_score, s.churn_reason,
       s.open_ticket_count, s.has_open_outage, s.clv_at_risk_usd, s.risk_band,
       s.service_summary,
       r.recommended_offer, r.predicted_retained_clv_usd
FROM dev_brendan_byam_streamline_telco.synced_subscriber_position s
LEFT JOIN dev_brendan_byam_streamline_telco.synced_retention_recommendations r
  ON s.subscriber_id = r.subscriber_id
WHERE s.risk_band IN ('critical', 'elevated')
ORDER BY s.clv_at_risk_usd DESC
LIMIT 50;
