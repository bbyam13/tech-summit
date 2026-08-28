"""Streamline Retention Agent — Databricks App
Layer 1: Visualize (live ranked view of at-risk subscribers)
Layer 2: Assist (AI explains risk, what-if, drafts memo)
Layer 3: Act (write action to Postgres with approval)
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
    """Load ranked at-risk subscribers from synced tables."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(VIEW_QUERY)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        conn.close()
        # Format for display
        data = []
        for row in rows:
            r = dict(zip(columns, row))
            data.append([
                r["subscriber_id"],
                r["risk_band"].upper(),
                f"${r['clv_at_risk_usd']:,.0f}",
                f"{r['churn_risk_score']:.0%}",
                r["churn_reason"],
                r["plan_type"],
                f"{r['tenure_months']}mo",
                f"${r['monthly_arpu_usd']:.0f}",
                r["recommended_offer"] or "—",
                r["service_node_id"],
                r["service_summary"][:80] + "..." if r["service_summary"] and len(r["service_summary"]) > 80 else (r["service_summary"] or "")
            ])
        return data
    except Exception as e:
        return [[f"Error: {e}", "", "", "", "", "", "", "", "", "", ""]]

# --- Layer 2: ASSIST ---
def search_notes(query):
    """BM25 search over retention_actions notes."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT subscriber_id, action_type, outcome, priority_score, notes
            FROM retention_actions
            WHERE to_tsvector('english', notes) @@ websearch_to_tsquery('english', %s)
            ORDER BY ts_rank(to_tsvector('english', notes), websearch_to_tsquery('english', %s)) DESC
            LIMIT 5
        """, (query, query))
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in cur.fetchall()]
        conn.close()
        return results
    except Exception as e:
        return [{"error": str(e)}]

def get_subscriber_detail(subscriber_id):
    """Get full subscriber detail for AI explanation."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT s.*, r.recommended_offer, r.predicted_retained_clv_usd, r.predicted_net_value_usd
            FROM dev_brendan_byam_streamline_telco.synced_subscriber_position s
            LEFT JOIN dev_brendan_byam_streamline_telco.synced_retention_recommendations r
              ON s.subscriber_id = r.subscriber_id
            WHERE s.subscriber_id = %s
        """, (subscriber_id,))
        columns = [desc[0] for desc in cur.description]
        row = cur.fetchone()
        conn.close()
        if row:
            return dict(zip(columns, row))
        return None
    except Exception as e:
        return {"error": str(e)}

def assist_chat(message, history):
    """AI assistant that explains risk and suggests actions."""
    from openai import OpenAI
    
    # Determine if this is about a specific subscriber
    sub_detail = None
    search_results = []
    subscriber_id = None
    
    # Extract subscriber ID if mentioned
    for word in message.split():
        if word.startswith("SUB-"):
            subscriber_id = word.strip(".,;:")
            sub_detail = get_subscriber_detail(subscriber_id)
            break
    
    # Search notes for relevant context
    search_results = search_notes(message)
    
    # Build context
    context = "You are a retention analyst assistant for Streamline Telco.\n"
    context += "Answer the hero question: 'Why is this subscriber at risk, and what do I offer?'\n\n"
    
    if sub_detail and not isinstance(sub_detail, dict) or (isinstance(sub_detail, dict) and "error" not in sub_detail):
        context += f"SUBSCRIBER DETAIL:\n{json.dumps(sub_detail, indent=2, default=str)}\n\n"
    
    if search_results and not any("error" in r for r in search_results):
        context += f"RELEVANT PRIOR ACTIONS (from BM25 search):\n{json.dumps(search_results, indent=2, default=str)}\n\n"
    
    context += "Provide: 1) Why at risk, 2) Recommended offer with rationale, 3) Predicted outcome.\n"
    context += "For what-if questions, reason about how changing variables affects churn probability.\n"
    
    try:
        client = OpenAI(
            api_key=os.environ.get("DATABRICKS_TOKEN", ""),
            base_url=os.environ.get("DATABRICKS_HOST", "https://fe-sandbox-bbyam-tech-summit.cloud.databricks.com") + "/serving-endpoints"
        )
        messages = [{"role": "system", "content": context}]
        for h in history:
            messages.append({"role": "user", "content": h[0]})
            if h[1]:
                messages.append({"role": "assistant", "content": h[1]})
        messages.append({"role": "user", "content": message})
        
        response = client.chat.completions.create(
            model="databricks-claude-sonnet-4",
            messages=messages,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        # Fallback: generate response from data alone
        if sub_detail and isinstance(sub_detail, dict) and "error" not in sub_detail:
            risk = sub_detail.get("churn_risk_score", "?")
            reason = sub_detail.get("churn_reason", "?")
            offer = sub_detail.get("recommended_offer", "?")
            clv = sub_detail.get("clv_at_risk_usd", "?")
            summary = sub_detail.get("service_summary", "")
            return (f"**Why at risk**: {summary}\n\n"
                    f"**Risk score**: {risk} | **Reason**: {reason} | **CLV at risk**: ${clv}\n\n"
                    f"**Recommended offer**: {offer}\n\n"
                    f"**Prior actions**: {json.dumps(search_results[:2], default=str)}\n\n"
                    f"(AI model unavailable: {e})")
        return f"Please specify a subscriber ID (e.g. SUB-0000214). Error: {e}"

def draft_memo(subscriber_id):
    """Auto-draft a retention memo for a subscriber."""
    detail = get_subscriber_detail(subscriber_id)
    if not detail or "error" in detail:
        return f"Could not find subscriber {subscriber_id}"
    
    memo = f"""# Retention Decision Memo

**Subscriber**: {detail.get('subscriber_id')}
**Date**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
**Agent**: Streamline Retention System

## Risk Assessment
- **Risk Score**: {detail.get('churn_risk_score', 'N/A')}
- **Risk Band**: {detail.get('risk_band', 'N/A')}
- **Churn Reason**: {detail.get('churn_reason', 'N/A')}
- **CLV at Risk**: ${detail.get('clv_at_risk_usd', 0):,.2f}

## Subscriber Profile
- **Plan**: {detail.get('plan_type', 'N/A')}
- **Tenure**: {detail.get('tenure_months', 'N/A')} months
- **ARPU**: ${detail.get('monthly_arpu_usd', 0):.2f}/mo
- **Node**: {detail.get('service_node_id', 'N/A')}
- **Metro**: {detail.get('home_metro', 'N/A')}

## Service Summary
{detail.get('service_summary', 'N/A')}

## Recommendation
- **Offer**: {detail.get('recommended_offer', 'N/A')}
- **Predicted Retained CLV**: ${detail.get('predicted_retained_clv_usd', 0):,.2f}
- **Net Value**: ${detail.get('predicted_net_value_usd', 0):,.2f}

## Decision
- [ ] Approve recommended offer
- [ ] Escalate to manager
- [ ] Custom offer: _______________

**Approver**: _______________  
**Signature**: _______________
"""
    return memo

# --- Layer 3: ACT ---
def submit_action(subscriber_id, action_type, offer_id, notes, approver):
    """Write a retention action to Postgres with approval."""
    if not subscriber_id or not action_type:
        return "Error: subscriber_id and action_type are required."
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO retention_actions
                (subscriber_id, action_type, offer_id, agent_id, outcome, notes)
            VALUES (%s, %s, %s, %s, 'pending', %s)
            RETURNING action_id, created_at
        """, (subscriber_id, action_type, offer_id or None, approver or 'app-user', notes or ''))
        result = cur.fetchone()
        conn.close()
        return f"Action #{result[0]} created at {result[1]}. Status: PENDING approval."
    except Exception as e:
        return f"Error: {e}"

def approve_action(action_id, approver):
    """Approve a pending action."""
    if not action_id:
        return "Error: action_id required."
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE retention_actions
            SET outcome = 'approved', agent_id = %s, updated_at = NOW()
            WHERE action_id = %s AND outcome = 'pending'
            RETURNING action_id, subscriber_id, outcome
        """, (approver or 'app-approver', int(action_id)))
        result = cur.fetchone()
        conn.close()
        if result:
            return f"Action #{result[0]} for {result[1]} APPROVED by {approver}."
        return "No pending action found with that ID."
    except Exception as e:
        return f"Error: {e}"

def load_pending_actions():
    """Load pending actions for approval queue."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT action_id, subscriber_id, action_type, offer_id, notes, 
                   outcome, agent_id, created_at
            FROM retention_actions
            ORDER BY created_at DESC
            LIMIT 20
        """)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        conn.close()
        data = []
        for row in rows:
            r = dict(zip(columns, row))
            data.append([
                r["action_id"],
                r["subscriber_id"],
                r["action_type"],
                r["offer_id"] or "—",
                r["outcome"],
                r["agent_id"],
                str(r["created_at"])[:19],
                r["notes"][:60] + "..." if r["notes"] and len(r["notes"]) > 60 else (r["notes"] or "")
            ])
        return data
    except Exception as e:
        return [[f"Error: {e}", "", "", "", "", "", "", ""]]

# --- GRADIO UI ---
with gr.Blocks(title="Streamline Retention Agent", theme=gr.themes.Base()) as app:
    gr.Markdown("# Streamline Retention Agent\n*Why is this subscriber at risk, and what do I offer?*")
    
    with gr.Tabs():
        # --- TAB 1: VISUALIZE ---
        with gr.Tab("Risk View"):
            gr.Markdown("### At-Risk Subscribers (ranked by CLV at risk)")
            refresh_btn = gr.Button("Refresh", variant="primary")
            risk_table = gr.Dataframe(
                headers=["Subscriber", "Risk", "CLV at Risk", "Score", "Reason", 
                         "Plan", "Tenure", "ARPU", "Offer", "Node", "Summary"],
                interactive=False
            )
            refresh_btn.click(fn=load_at_risk_subscribers, outputs=risk_table)
        
        # --- TAB 2: ASSIST ---
        with gr.Tab("Assistant"):
            gr.Markdown("### Retention Assistant\nAsk about a subscriber (e.g. 'Why is SUB-0000214 at risk?') or explore what-if scenarios.")
            chatbot = gr.ChatInterface(
                fn=assist_chat,
                examples=[
                    "Why is SUB-0000214 at risk and what should I offer?",
                    "What if we offer a loyalty discount instead of bill credit to SUB-0000214?",
                    "Show me prior actions for outage-related churn on NODE-OHIO-14"
                ]
            )
            gr.Markdown("### Draft Memo")
            with gr.Row():
                memo_sub_id = gr.Textbox(label="Subscriber ID", placeholder="SUB-0000214")
                memo_btn = gr.Button("Generate Memo")
            memo_output = gr.Markdown()
            memo_btn.click(fn=draft_memo, inputs=memo_sub_id, outputs=memo_output)
        
        # --- TAB 3: ACT ---
        with gr.Tab("Actions"):
            gr.Markdown("### Submit Retention Action")
            with gr.Row():
                act_sub_id = gr.Textbox(label="Subscriber ID", placeholder="SUB-0000214")
                act_type = gr.Dropdown(
                    choices=["offer_presented", "follow_up", "escalation"],
                    label="Action Type"
                )
                act_offer = gr.Dropdown(
                    choices=["bill_credit", "loyalty_discount", "upgrade_offer", "contract_extension", "service_bundle"],
                    label="Offer"
                )
            act_notes = gr.Textbox(label="Notes", lines=2)
            act_approver = gr.Textbox(label="Your Name/ID", placeholder="agent-jsmith")
            submit_btn = gr.Button("Submit Action", variant="primary")
            submit_result = gr.Textbox(label="Result", interactive=False)
            submit_btn.click(
                fn=submit_action,
                inputs=[act_sub_id, act_type, act_offer, act_notes, act_approver],
                outputs=submit_result
            )
            
            gr.Markdown("### Approve / Review Actions")
            with gr.Row():
                approve_id = gr.Number(label="Action ID to Approve", precision=0)
                approve_name = gr.Textbox(label="Approver Name", placeholder="mgr-jones")
                approve_btn = gr.Button("Approve", variant="secondary")
            approve_result = gr.Textbox(label="Result", interactive=False)
            approve_btn.click(
                fn=approve_action,
                inputs=[approve_id, approve_name],
                outputs=approve_result
            )
            
            gr.Markdown("### Action Log")
            actions_refresh = gr.Button("Refresh Actions")
            actions_table = gr.Dataframe(
                headers=["ID", "Subscriber", "Type", "Offer", "Status", "Agent", "Created", "Notes"],
                interactive=False
            )
            actions_refresh.click(fn=load_pending_actions, outputs=actions_table)
    
    # Auto-load on start
    app.load(fn=load_at_risk_subscribers, outputs=risk_table)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=8000)
