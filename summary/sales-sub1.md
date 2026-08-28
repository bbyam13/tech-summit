# Build 1 — How We Solved the Problem

## The Problem

> Frontline teams miss critical business events because decisions run on high-latency batch data that the operational app cannot reach.

Streamline Telco's retention agents couldn't act fast enough. When NODE-OHIO-14 went down in Columbus, 200 subscribers started churning — but the signals lived in the Lakehouse while the retention app ran on a separate, stale database. By the time agents saw the risk, customers were already gone.

## How Lakebase Closes the Gap

### One platform for analytical and operational data

Lakebase sits inside Unity Catalog. The same gold-layer subscriber 360 that powers our AI/BI dashboard syncs directly into Postgres — no ETL pipelines to a separate OLTP store, no data copies drifting out of sync. Retention agents query `synced_subscriber_position` at sub-millisecond latency and get the same governed data that analytics sees. One platform, one source of truth.

### Safe copy of production in seconds

We created `dev-retention-schema` off production with a single API call. A full copy of the operational database — tables, indexes, data — available instantly via copy-on-write branching. The team iterated on schema changes, tested seed data, and validated search indexes without touching the live instance. When NODE-OHIO-14 hit, we could experiment with priority-scoring logic on the branch while production kept serving the retention app.

### Coding agent evolves the schema safely

Genie Code (our coding agent) authored a schema migration on the dev branch: a `priority_score` column that lets the ML model triage which subscribers to call first. The agent wrote the DDL, created a composite index for the retention workflow's access pattern, backfilled scores using business rules, validated the result, and promoted the change to production — all tracked in git with a `Co-authored-by: Genie Code` trailer. No human wrote the migration. The agent shipped it safely because branching made it impossible to break production.

### Native hybrid search without external services

We installed `lakebase_text` (BM25) directly in Postgres and indexed the `notes` column on `retention_actions`. An assistant can now search "outage bill credit service restored" and instantly find that SUB-0000214 was retained after a bill credit — no Elasticsearch cluster, no vector database, no data leaving the platform. The search lives where the data lives.

## The Result

The retention app now runs on Lakebase with:
- Real-time subscriber 360 (synced from the Lakehouse)
- Writable action tracking (every offer, follow-up, and outcome)
- Bidirectional sync back to Delta (SCD Type 2 history for model retraining)
- Full-text search over agent notes
- Schema evolution via coding agents on safe branches

SUB-0000214 — a 5-year customer worth $2,500+ in CLV — was flagged, offered a bill credit, and retained. All within the platform. No external services. No batch lag. No risk to production.

That's the governed operational data layer the app runs on, and the modern development workflow that makes shipping on it safe.
