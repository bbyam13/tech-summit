-- Silver: per-subscriber billing rollup
-- has_recent_dispute, last_dispute_reason

CREATE OR REFRESH MATERIALIZED VIEW silver_billing
AS
SELECT
  subscriber_id,
  MAX(CASE WHEN disputed = TRUE THEN TRUE ELSE FALSE END) AS has_recent_dispute,
  FIRST(dispute_reason) AS last_dispute_reason
FROM (
  SELECT
    subscriber_id,
    bill_month,
    amount_usd,
    disputed,
    dispute_reason,
    ROW_NUMBER() OVER (PARTITION BY subscriber_id ORDER BY bill_month DESC) AS rn
  FROM read_files('/Volumes/${catalog}/${schema}/raw_data/billing/')
  WHERE bill_month >= CURRENT_DATE - INTERVAL 90 DAYS
)
GROUP BY subscriber_id;
