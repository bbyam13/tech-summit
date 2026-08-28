-- Gold: ranked retention offer per open at-risk subscriber (HEURISTIC)
-- For each at-risk subscriber, construct 3 candidate offers, rank by net value.
-- bill_credit wins for service-reason (the hero case).

CREATE OR REFRESH MATERIALIZED VIEW gold_retention_recommendations
AS
WITH candidates AS (
  SELECT
    subscriber_id,
    churn_reason,
    clv_at_risk_usd,
    monthly_arpu_usd,

    -- Bill credit
    CASE WHEN churn_reason = 'service' THEN 0.7 ELSE 0.3 END AS bc_p_retain,
    50.0 AS bc_cost,

    -- Plan upgrade discount
    CASE WHEN churn_reason = 'price' THEN 0.65 ELSE 0.3 END AS pu_p_retain,
    ROUND(monthly_arpu_usd * 0.2 * 12, 2) AS pu_cost,

    -- Device upgrade
    CASE WHEN churn_reason = 'device' THEN 0.6 ELSE 0.25 END AS du_p_retain,
    300.0 AS du_cost

  FROM gold_open_atrisk
),
scored AS (
  SELECT
    subscriber_id,
    churn_reason,
    clv_at_risk_usd,
    monthly_arpu_usd,

    -- Bill credit retained CLV and net value
    ROUND(clv_at_risk_usd * bc_p_retain, 2) AS bc_retained_clv,
    ROUND(clv_at_risk_usd * bc_p_retain - bc_cost, 2) AS bc_net,
    bc_cost,

    -- Plan upgrade discount retained CLV and net value
    ROUND(clv_at_risk_usd * pu_p_retain, 2) AS pu_retained_clv,
    ROUND(clv_at_risk_usd * pu_p_retain - pu_cost, 2) AS pu_net,
    pu_cost,

    -- Device upgrade retained CLV and net value
    ROUND(clv_at_risk_usd * du_p_retain, 2) AS du_retained_clv,
    ROUND(clv_at_risk_usd * du_p_retain - du_cost, 2) AS du_net,
    du_cost

  FROM candidates
)
SELECT
  subscriber_id,
  -- recommended_offer = argmax(net_value)
  CASE
    WHEN bc_net >= pu_net AND bc_net >= du_net THEN 'bill_credit'
    WHEN pu_net >= bc_net AND pu_net >= du_net THEN 'plan_upgrade_discount'
    ELSE 'device_upgrade'
  END AS recommended_offer,
  -- predicted_retained_clv_usd for the recommended offer
  CASE
    WHEN bc_net >= pu_net AND bc_net >= du_net THEN bc_retained_clv
    WHEN pu_net >= bc_net AND pu_net >= du_net THEN pu_retained_clv
    ELSE du_retained_clv
  END AS predicted_retained_clv_usd,
  -- predicted_net_value_usd for the recommended offer
  CASE
    WHEN bc_net >= pu_net AND bc_net >= du_net THEN bc_net
    WHEN pu_net >= bc_net AND pu_net >= du_net THEN pu_net
    ELSE du_net
  END AS predicted_net_value_usd,
  -- offer_ranking: JSON array of all three options
  TO_JSON(ARRAY(
    NAMED_STRUCT('offer_type', 'bill_credit', 'retained_clv', bc_retained_clv, 'net_value', bc_net, 'cost', bc_cost),
    NAMED_STRUCT('offer_type', 'plan_upgrade_discount', 'retained_clv', pu_retained_clv, 'net_value', pu_net, 'cost', pu_cost),
    NAMED_STRUCT('offer_type', 'device_upgrade', 'retained_clv', du_retained_clv, 'net_value', du_net, 'cost', du_cost)
  )) AS offer_ranking,
  CURRENT_TIMESTAMP() AS scored_at
FROM scored;
