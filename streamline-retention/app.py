"""Streamline Retention Agent — Databricks App
Layer 1: Visualize (live ranked view of at-risk subscribers)
"""
import os
import json
import gradio as gr
import psycopg
from datetime import datetime, timezone
from databricks.sdk import WorkspaceClient

# --- DB Connection (uses injected env vars from Lakebase resource on production) ---
PROD_ENDPOINT = "projects/telco-project/branches/production/endpoints/primary"

def get_connection():
    w = WorkspaceClient()
    cred = w.postgres.generate_database_credential(endpoint=PROD_ENDPOINT)
    return psycopg.connect(
        host=os.environ.get("PGHOST"),
        port=int(os.environ.get("PGPORT", 5432)),
        dbname=os.environ.get("PGDATABASE", "databricks_postgres"),
        user=os.environ.get("PGUSER", ""),
        password=cred.token,
        sslmode="require", autocommit=True
    )

# --- Layer 1: VISUALIZE ---
VIEW_QUERY = """
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
LIMIT 50
"""

def load_at_risk_subscribers():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(VIEW_QUERY)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        conn.close()
        data = []
        for row in rows:
            r = dict(zip(columns, row))
            data.append([
                r["subscriber_id"], r["risk_band"].upper(),
                f"${r['clv_at_risk_usd']:,.0f}", f"{r['churn_risk_score']:.0%}",
                r["churn_reason"], r["plan_type"], f"{r['tenure_months']}mo",
                f"${r['monthly_arpu_usd']:.0f}", r["recommended_offer"] or "—",
                r["service_node_id"],
                r["service_summary"][:80] + "..." if r["service_summary"] and len(r["service_summary"]) > 80 else (r["service_summary"] or "")
            ])
        return data
    except Exception as e:
        return [[f"Error: {e}", "", "", "", "", "", "", "", "", "", ""]]

with gr.Blocks(title="Streamline Retention Agent", theme=gr.themes.Base()) as app:
    gr.Markdown("# Streamline Retention Agent\n*Why is this subscriber at risk, and what do I offer?*")
    with gr.Tabs():
        with gr.Tab("Risk View"):
            gr.Markdown("### At-Risk Subscribers (ranked by CLV at risk)")
            refresh_btn = gr.Button("Refresh", variant="primary")
            risk_table = gr.Dataframe(
                headers=["Subscriber", "Risk", "CLV at Risk", "Score", "Reason",
                         "Plan", "Tenure", "ARPU", "Offer", "Node", "Summary"],
                interactive=False
            )
            refresh_btn.click(fn=load_at_risk_subscribers, outputs=risk_table)
    app.load(fn=load_at_risk_subscribers, outputs=risk_table)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=8000)
