-- Gold: retention-offer history for model training
-- One row per historical offer with features + outcome

CREATE OR REFRESH MATERIALIZED VIEW gold_retention_outcomes
AS
SELECT
  retention_id,
  subscriber_id,
  offer_type,
  churn_reason,
  monthly_arpu_usd,
  offer_cost_usd,
  retained,
  retained_clv_usd
FROM silver_retention;
