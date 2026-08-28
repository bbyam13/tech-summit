-- Query against the synced Unity Catalog table in Lakebase Postgres
-- Source: bbyam_ts.dev_brendan_byam_streamline_telco.gold_subscriber_position
-- Synced to: databricks_postgres.synced_subscriber_position
SELECT * FROM synced_subscriber_position LIMIT 5;
