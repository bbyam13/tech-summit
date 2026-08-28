# Technical Summary — Build 1 (Lakebase)

## Project
- **Project**: `telco-project`
- **UC Catalog**: `bbyam_ts`
- **Schema**: `dev_brendan_byam_streamline_telco`

## Lakebase Instance
| Property | Value |
|----------|-------|
| Endpoint | `projects/telco-project/branches/production/endpoints/primary` |
| Port | 5432 |
| Database | `databricks_postgres` |
| SSL | require |
| Auth | OAuth token via `w.postgres.generate_database_credential()` |
| Version | PostgreSQL 17.11 |

## Branches
| Branch | ID | Purpose |
|--------|----|---------|
| production | `br-withered-dust-d20vsxri` | Live operational data |
| dev-retention-schema | `br-nameless-frost-d2nw08ds` | Schema iteration + experiments |

## Tables (production, `public` schema)

### Writable (app state)
| Table | Columns | Notes |
|-------|---------|-------|
| `retention_actions` | action_id, subscriber_id, action_type, offer_id, agent_id, outcome, notes, created_at, updated_at, priority_score | CHECK constraints on action_type/outcome, REPLICA IDENTITY FULL |
| `offers_catalog` | offer_id, offer_name, description, discount_pct, duration_months, eligible_plans[], active | Reference data, 5 offers seeded |

### Synced from UC (read-only, schema `dev_brendan_byam_streamline_telco`)
| Table | Source | Key columns |
|-------|--------|-------------|
| `synced_subscriber_position` | `gold_subscriber_position` | subscriber_id, plan_type, tenure_months, monthly_arpu_usd, service_node_id, churn_risk_score, clv_at_risk_usd, risk_band, service_summary |
| `synced_retention_recommendations` | `gold_retention_recommendations` | subscriber_id, recommended_offer, predicted_retained_clv_usd, offer_ranking JSON |

## Extensions
| Extension | Version | Purpose |
|-----------|---------|--------|
| vector | 0.8.0 | pgvector embeddings |
| lakebase_vector | 1.1.0 | Managed ANN indexes |
| lakebase_text | 0.1.1 | BM25 full-text search |

## Indexes (dev branch)
- `idx_retention_actions_subscriber_outcome` — composite (subscriber_id, outcome, created_at DESC)
- `idx_retention_notes_bm25` — `USING lakebase_bm25 ((to_tsvector('english', notes)))`

## CDF Reverse Sync
- **Source**: `public.retention_actions` (dev branch)
- **Destination**: `alex_feng.default.lb_retention_actions_history`
- **Type**: SCD Type 2
- **System columns**: `_pg_change_type`, `_pg_lsn`, `_pg_xid`, `_timestamp`, `_sort_by`

## Connection Pattern (Python)
```python
from databricks.sdk import WorkspaceClient
import psycopg

w = WorkspaceClient()
ep = w.postgres.get_endpoint(name="projects/telco-project/branches/production/endpoints/primary")
host = ep.status.hosts.host
cred = w.postgres.generate_database_credential(endpoint=ep.name)

conn = psycopg.connect(
    host=host, port=5432, dbname="databricks_postgres",
    user="brendan.byam@databricks.com", password=cred.token,
    sslmode="require"
)
```

## Agentic Schema Change
- **What**: Added `priority_score NUMERIC(5,2)` + composite index to `retention_actions`
- **Author**: Genie Code (Co-authored-by trailer in git)
- **Flow**: Created on dev branch → validated → promoted to production
- **Git**: `dev-retention-schema` branch merged to `main` with --no-ff

## Search Query Pattern
```sql
SELECT subscriber_id, action_type, outcome, notes,
       ts_rank(to_tsvector('english', notes), websearch_to_tsquery('english', $1)) AS score
FROM retention_actions
WHERE to_tsvector('english', notes) @@ websearch_to_tsquery('english', $1)
ORDER BY score DESC;
```

## Submission Evidence
All artifacts in `/submission1/`: connectivity_check.json, synced_table.sql, synced_table_result.json, reverse_sync_sample.json, branch.txt, agent_change/*, search_query.txt, search_result.json, core_question.txt, core_query.sql, core_query_result.json, git_history.txt
