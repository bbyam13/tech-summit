-- Gold: current at-risk subscribers with candidate offer + reason context
-- Used by the churn model (scoring input) and app care queue

CREATE OR REFRESH MATERIALIZED VIEW gold_open_atrisk
AS
SELECT
  subscriber_id,
  plan_type,
  tenure_months,
  monthly_arpu_usd,
  service_node_id,
  home_metro,
  sub_lat,
  sub_lng,
  churn_risk_score,
  clv_at_risk_usd,
  churn_reason,
  has_open_outage,
  has_open_billing,
  open_ticket_count,
  -- Candidate offer matched to the churn reason
  CASE churn_reason
    WHEN 'service' THEN 'bill_credit'
    WHEN 'price'   THEN 'plan_upgrade_discount'
    WHEN 'device'  THEN 'device_upgrade'
    ELSE 'bill_credit'
  END AS candidate_offer_id
FROM gold_subscriber_position
WHERE risk_band IN ('critical', 'elevated', 'watch');
