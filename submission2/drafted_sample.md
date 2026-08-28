# Retention Decision Memo

**Subscriber**: SUB-0000214
**Date**: 2026-08-28 01:25 UTC
**Agent**: Streamline Retention System (auto-drafted)

## Risk Assessment
- **Risk Score**: 0.84 (critical)
- **Risk Band**: CRITICAL
- **Churn Reason**: service (NODE-OHIO-14 outage)
- **CLV at Risk**: $2,726.44

## Subscriber Profile
- **Plan**: broadband
- **Tenure**: 60 months (5 years)
- **ARPU**: $115.27/mo
- **Node**: NODE-OHIO-14 (Columbus, OH)
- **Open Tickets**: 1 (outage-related)
- **Has Open Outage**: true

## Service Summary
Long-tenure broadband subscriber impacted by NODE-OHIO-14 outage. Filed billing dispute after service disruption. Risk elevated from baseline 0.3 to 0.84 following outage event. Previously stable customer with no prior churn signals.

## Prior Actions (BM25 search: "outage bill credit service restored")
- Action #2: follow_up by agent-rnakamura -> RETAINED
  "Subscriber accepted bill credit after follow-up call. Confirmed service restored post-outage."

## Model Recommendation
- **Offer**: bill_credit
- **Confidence**: 92%
- **Predicted Retained CLV**: $2,100.00
- **Net Value**: +$2,050 (credit cost ~$50 vs CLV at risk $2,500+)

## Decision
- [x] Approve recommended offer (bill_credit)
- [ ] Escalate to manager
- [ ] Custom offer

**Submitted by**: agent-care-jsmith (via app)
**Approved by**: mgr-jones
**Action ID**: 13
**Decision Chain**: risk_trigger -> offer_recommended -> action_submitted -> action_approved
