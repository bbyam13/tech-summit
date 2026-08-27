# Workshop - Streamline Telco (Churn Save on the Call)

**The use case, in plain words:** Streamline is a broadband + mobile carrier. A network outage on one service node collided with a billing problem, and a cluster of subscribers is **about to cancel** — the save moment is on the call, but agents working from last-night's screen can't see the history in time. You build an app that spots each at-risk subscriber, explains **why** they're at risk, recommends the best offer — **a bill credit, a plan discount, or a device upgrade** — matched to the reason, and lets a care lead approve it in one click. The data, the recommendation, and the AI that assists are all governed on Databricks, fast enough for a full contact center, with AI spend that stays predictable per call.

## 🎓 Start here — you build this, it isn't pre-built

Starting point for the Tech Summit FY27 Live Days **AI Customer Challenge**. It ships the **data
generator + specs + a bootstrap app** — **you build the solution** (that's the exercise). Build like
a citizen developer: **describe your intent to Genie Code and iterate**. Work carries forward
step by step.

### ▶️ How to start

**1. Get the template into your workspace.** Download it from **go/solution-builder** and import the folder into your Databricks workspace (Workspace → *Import*). Everything you need travels with it — work directly from there.

**2. Open a Genie Code session** in that folder and kick it off with this prompt:

> *"Read `README.md`, then all the files under `specifications/`, to build up the full context of
> this workshop — the story, the data model, and each component I need to create. Then read
> `data_generation/generate_data.py` to understand how the raw data is structured. Before doing
> anything, ask me which **catalog and schema** to use. Then run `data_generation/generate_data.py`
> as a **job run** into that catalog/schema to load the raw data. Put all the files you create in
> this project folder — transformation code under `./transformation`, and the dashboard, Genie
> space, and everything else at the root (`./`)."*

From there, build the solution one component at a time — SDP pipeline, dashboard, Genie, Lakebase, app, gateway.

**3. Build the solution**, iterating with Genie Code, using the per-component detail in `specifications/`. For the app, point your agent at `app/APP_WORKSHOP.md`.

Everything below is the **story + reference spec** the build should realize. The `specifications/`
folder has the full detail per component; `resources.json` lists the capabilities.

---

## The Story

| | |
|---|---|
| **Company** | Streamline Telco — broadband + mobile + streaming (~$3.2B revenue, ~4M subscribers, ~$68 ARPU) |
| **Hero** | Rae Nakamura, SVP Customer Care & Retention (non-technical) |
| **Problem** | A network outage on one node collided with billing friction, pushing a cluster of subscribers into churn risk |
| **Investigation** | Rae asks *"Why is SUB-0000214 at risk, and what should I offer?"* — the platform surfaces the reason (service, not price) and ranks bill credit vs. plan discount vs. device upgrade |
| **Root cause** | The save moment is on the call, but agents on last-night's screen can't see the outage + billing history in time |
| **Impact** | ~$0.4M CLV at risk on the sampled at-risk cohort (~$3.9M/yr at the full 4M-subscriber base per 0.1pt of monthly churn avoided), ~350 open tickets — concentrated on the outage node |

---

## Overview

Rae Nakamura (SVP Customer Care & Retention) opens the retention console and sees a red cluster on one chart: valuable, long-tenured subscribers whose churn risk spiked after a node outage collided with a billing issue. She reviews the worst account — *"Why is SUB-0000214 at risk, and what do I offer?"* — and the app surfaces the reason (service, not price), ranks **bill credit / plan discount / device upgrade** by retained CLV, recommends the bill credit (it acknowledges the outage), drafts the call-resolution summary, and writes it back after she approves. Governed subscriber data, a governed recommendation, and a governed AI assistant — fast at full contact-center concurrency, with AI spend predictable per call.

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Subscribers (sampled) | ~40,000 (the ~4M base is talking-track) |
| Plans | broadband / mobile / bundle |
| Hero subscriber | SUB-0000214 — 5-year, on outage node NODE-OHIO-14, open billing ticket, churn risk ~0.86, reason = service |
| Outage onset | ~3 weeks ago (dynamic — `OUTAGE_ONSET = NOW − 3 weeks`) |
| At-risk subscribers (critical/elevated) | ~200 — all service-reason (open tickets + billing disputes on the outage node), each with real evidence behind the "why" |
| CLV at risk (sampled) | ~$0.4M (full-base figure ~$3.9M/yr — talking-track) |
| Retention offer ranked by model | bill credit / plan discount / device upgrade + predicted retained CLV |
| Assistant AI spend | Capped, predictable per call at full contact-center concurrency |

---

## The demo arc (what the finished solution shows)

1. **See it** — open the Care Desk app: a churn-risk scatter, a red cluster of valuable subscribers at risk, with CLV-at-risk + open-ticket KPIs.
2. **Ask why** — in the chat dock, ask why SUB-0000214 is at risk; the assistant investigates via Genie + the service history over the governed lakehouse.
3. **Get the offer** — the assistant surfaces the reason (service) and ranks bill credit / plan discount / device upgrade by retained CLV, recommending the bill credit, with a what-if.
4. **Act** — approve → the retention offer writes back to Lakebase → the queue and KPIs update live.
5. **Governed AI** — every assistant call runs through Unity AI Gateway (spend cap, guardrails, per-call logging), predictable at contact-center scale.

Full per-component detail is in `specifications/`.
