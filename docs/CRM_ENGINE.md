# CRM & Sales Pipeline Engine

> Sprint 6.3 — enterprise lead management, sales pipeline, and AI-assisted sales

## Overview

Sprint 6.3 delivers a complete **CRM Engine** and **Sales Pipeline** for the Auto Marketplace, integrated with AI Platform Core v3.0 via bridges only.

---

## Architecture

```mermaid
flowchart TB
    subgraph CRM Engine
        CE[CRMEngine]
        LE[LeadService]
        DE[DealService]
        SP[SalesPipelineEngine]
        AI[AISalesAssistant]
        WF[CRMWorkflowBridge]
        SEC[CRMSecurity]
    end

    subgraph Modules
        ACT[activities]
        COM[communications]
        TSK[tasks]
        CAL[calendar]
    end

    CE --> LE & DE & SP & AI & WF
    CE --> ACT & COM & TSK & CAL
    AI -.-> Platform Core
    WF -.-> Workflow Engine
```

---

## Modules

| Module | Role |
|--------|------|
| `crm/` | Models, engine, events, AI assistant, security, workflow bridge |
| `sales_pipeline/` | Stage progression, forecasting, conversion analytics |
| `leads/` | Lead CRUD, scoring, qualification |
| `deals/` | Deal CRUD, win/loss tracking |
| `customers/` | CustomerProfile CRUD, segmentation |
| `activities/` | Interaction log, customer timeline |
| `communications/` | Phone calls, emails |
| `tasks/` | Task management |
| `calendar/` | Meetings, reminders |

---

## Domain Models

`CustomerProfile`, `CRMLead`, `LeadSource`, `CRMLeadStatus`, `SalesOpportunity`, `CRMDeal`, `DealStage`, `Contact`, `Interaction`, `Meeting`, `PhoneCall`, `EmailMessage`, `CRMTask`, `Reminder`, `SalesAgent`, `SalesTeam`

---

## CRM Guide

```python
from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.crm.models import CustomerProfile, CRMLead

# Customer
profile = await auto_marketplace.crm_engine.customers.create(
    CustomerProfile(first_name="John", email="john@example.com")
)

# Lead with AI scoring
lead = await auto_marketplace.crm_engine.leads.create(
    CRMLead(customer_id=profile.customer_id, vehicle_id="v1", dealer_id="d1")
)

# Qualify
await auto_marketplace.crm_engine.pipeline.qualify_lead(lead.lead_id, agent_id="agent-1")

# Timeline
timeline = auto_marketplace.crm_engine.activities.customer_timeline(profile.customer_id)
```

---

## Sales Pipeline Guide

### Stages
`prospect` → `qualification` → `proposal` → `negotiation` → `approval` → `closed_won` / `closed_lost`

```python
deal = await auto_marketplace.crm_engine.deals.create(CRMDeal(customer_id="c1", amount=35000))
await auto_marketplace.crm_engine.pipeline.advance_stage(deal.deal_id)
await auto_marketplace.crm_engine.deals.mark_won(deal.deal_id, amount=34000)

# Analytics
auto_marketplace.crm_engine.pipeline.pipeline_view(dealer_id="d1")
auto_marketplace.crm_engine.pipeline.conversion_analytics()
auto_marketplace.crm_engine.pipeline.forecast(days=30)
```

---

## AI Sales Assistant

| Capability | Description |
|------------|-------------|
| Lead scoring | Rule-based + Decision Engine bridge |
| Intent analysis | Reasoning Engine bridge |
| Next best action | Context-aware recommendations |
| Follow-up suggestions | Channel and timing |
| Conversation summary | Interaction summarization |
| Deal probability | Stage-based prediction |
| Customer segmentation | cold / warm / hot / vip |

---

## Workflow Integration

- Automatic lead assignment workflows
- Follow-up scheduling
- Manager notifications
- Task automation
- Deal approval workflows

---

## Security — CRM Roles

| Role | Permissions |
|------|-------------|
| Owner | Full access |
| Administrator | CRM management |
| Sales Manager | Pipeline, leads, deals, reports |
| Sales Agent | Read/write leads, deals, tasks |
| Dealer | Read-only CRM |
| Customer | Self-service read |
| AI Agent | Scoring, predictions, suggestions |

---

## Events

`LeadCreated`, `LeadQualified`, `DealOpened`, `DealUpdated`, `DealWon`, `DealLost`, `CustomerCreated`, `TaskCreated`, `ReminderTriggered`

---

## API — `/api/auto/v1/crm`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/metrics` | CRM metrics |
| GET/POST | `/customers` | Customer profiles |
| GET | `/customers/{id}/timeline` | Activity timeline |
| GET/POST | `/leads` | Leads |
| POST | `/leads/{id}/qualify` | Qualify lead |
| GET | `/leads/{id}/next-action` | AI next action |
| GET/POST | `/deals` | Deals |
| POST | `/deals/{id}/advance` | Advance stage |
| POST | `/deals/{id}/win` | Mark won |
| POST | `/deals/{id}/lose` | Mark lost |
| GET | `/pipeline` | Pipeline view |
| GET | `/pipeline/forecast` | Forecast |
| GET | `/pipeline/conversion` | Conversion analytics |
| GET/POST | `/tasks` | Tasks |
| POST | `/activities/calls` | Log call |
| POST | `/activities/emails` | Log email |
| POST | `/calendar/meetings` | Schedule meeting |

---

## Manifest

`application_version: "1.4.0-alpha"`

---

## Tests

```bash
pytest tests/test_crm_engine.py -q
```

---

## Developer Guide

Access via `auto_marketplace.crm_engine`. Sprint 6.1 legacy endpoints (`/leads`, `/customers`) remain unchanged.

```python
auto_marketplace.crm_engine.metrics()
auto_marketplace.crm_engine.security.authorize("sales_agent", "leads.write")
```
