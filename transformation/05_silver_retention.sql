-- Silver: retention-offer history denormalized
-- Powers the model training table (gold_retention_outcomes)

CREATE OR REFRESH MATERIALIZED VIEW silver_retention
AS
SELECT
  r.retention_id,
  r.subscriber_id,
  r.offer_type,
  r.churn_reason,
  r.monthly_arpu_usd,
  r.initiated_date,
  r.offer_cost_usd,
  r.retained,
  r.retained_clv_usd
FROM read_files('/Volumes/${catalog}/${schema}/raw_data/retention_offers/') r;
