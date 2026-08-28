-- Silver: per-subscriber ticket rollup
-- open_ticket_count, has_open_outage, has_open_billing, latest_ticket_type

CREATE OR REFRESH MATERIALIZED VIEW silver_tickets
AS
SELECT
  subscriber_id,
  COUNT(CASE WHEN closed_date IS NULL THEN 1 END) AS open_ticket_count,
  MAX(CASE WHEN ticket_type = 'outage' AND closed_date IS NULL THEN TRUE ELSE FALSE END) AS has_open_outage,
  MAX(CASE WHEN ticket_type = 'billing' AND closed_date IS NULL THEN TRUE ELSE FALSE END) AS has_open_billing,
  FIRST(ticket_type) AS latest_ticket_type
FROM (
  SELECT
    subscriber_id,
    ticket_type,
    opened_date,
    closed_date,
    channel,
    note_text,
    ROW_NUMBER() OVER (PARTITION BY subscriber_id ORDER BY opened_date DESC) AS rn
  FROM read_files('/Volumes/${catalog}/${schema}/raw_data/tickets/')
)
GROUP BY subscriber_id;
