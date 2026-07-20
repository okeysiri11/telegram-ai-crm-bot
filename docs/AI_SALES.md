# AI Sales Agents & Customer Intelligence

> Sprint 6.4 — autonomous AI sales assistants and customer intelligence on Platform Core v3.0

## Overview

Sprint 6.4 delivers **AI Sales Agents**, **Customer Intelligence**, and an **AI Recommendation Engine** integrated with CRM, Vehicle Catalog, and Platform Core via bridges only.

---

## Architecture

```mermaid
flowchart TB
    subgraph AISalesEngine
        AE[AISalesEngine]
        CI[CustomerIntelligence]
        REC[AIRecommendationEngine]
        CON[ConversationService]
        LI[LeadIntelligence]
        NEG[NegotiationService]
        KB[KnowledgeService]
    end

    subgraph Agents
        SA[SalesAgent]
        CA[CustomerAssistant]
        RA[RecommendationAgent]
        LQA[LeadQualificationAgent]
    end

    AE --> CI & REC & CON & LI & NEG & KB
    AE --> Agents
    AE -.-> Platform Core
    AE --> CRMEngine
    AE --> VehicleCatalog
```

---

## Modules

| Module | Role |
|--------|------|
| `ai_sales/` | Engine, agents, events, platform bridge, workflows |
| `customer_intelligence/` | Profile analysis, intent, budget, preferences |
| `recommendations/` | Personalized, upsell, cross-sell, trade-in, accessories |
| `conversation/` | Memory, summarization, sentiment, response suggestions |
| `lead_intelligence/` | Scoring, qualification, hot/warm/cold, deal value |
| `negotiation/` | Offer generation, counter-proposals |
| `knowledge/` | Sales knowledge base |

---

## AI Agents

| Agent | Purpose |
|-------|---------|
| `SalesAgent` | Sales workflow decisions |
| `CustomerAssistant` | Customer-facing chat |
| `DealerAssistant` | Dealer dashboard insights |
| `RecommendationAgent` | Vehicle recommendation orchestration |
| `LeadQualificationAgent` | Automatic lead qualification |
| `NegotiationAssistant` | Counter-offers and talking points |
| `FollowUpAgent` | Follow-up scheduling |
| `DeliveryAssistant` | Delivery planning |

---

## AI Agent Guide

```python
from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.ai_sales.models import AgentType

# Dispatch an agent
result = await auto_marketplace.ai_sales_engine.dispatch_agent(
    AgentType.CUSTOMER_ASSISTANT,
    {"message": "I need a family SUV under $45k"},
)

# Customer intelligence
intel = await auto_marketplace.ai_sales_engine.intelligence.analyze_profile(customer_id)
intent = await auto_marketplace.ai_sales_engine.intelligence.purchase_intent(customer_id)

# Lead intelligence
report = await auto_marketplace.ai_sales_engine.leads.analyze_lead(lead_id)
qualified = await auto_marketplace.ai_sales_engine.leads.qualify_lead(lead_id)
```

---

## Recommendation Guide

```python
# Personalized recommendations
items = await auto_marketplace.ai_sales_engine.recommendations.personalized(customer_id)

# Alternatives, upsell, cross-sell
alts = await auto_marketplace.ai_sales_engine.recommendations.alternatives(vehicle_id)
upsell = await auto_marketplace.ai_sales_engine.recommendations.upsell(customer_id, vehicle_id)
cross = await auto_marketplace.ai_sales_engine.recommendations.cross_sell(customer_id)

# Trade-in and accessories
trade_in = await auto_marketplace.ai_sales_engine.recommendations.trade_in_suggestions(customer_id)
accessories = await auto_marketplace.ai_sales_engine.recommendations.accessory_recommendations(vehicle_id)
```

---

## Conversation Guide

```python
session = await auto_marketplace.ai_sales_engine.conversations.start_session(customer_id)
await auto_marketplace.ai_sales_engine.conversations.append_turn(
    session.session_id, role="user", content="Interested in hybrid models"
)
summary = await auto_marketplace.ai_sales_engine.conversations.summarize(session.session_id)
suggestion = await auto_marketplace.ai_sales_engine.conversations.suggest_response(session.session_id)
context = auto_marketplace.ai_sales_engine.conversations.multi_channel_context(customer_id)
```

---

## Platform Integration

| Engine | Usage |
|--------|-------|
| Memory | Conversation context persistence |
| Reasoning | Intent analysis, summarization, negotiation |
| Planning | Purchase journey, delivery planning |
| Decision | Lead scoring, sales next steps |
| Learning | Interaction feedback |
| Workflow | Onboarding, nurturing, follow-ups, offers |
| Collaboration | Multi-agent deal sessions |
| CRM Engine | Leads, customers, deals |
| Vehicle Catalog | Recommendation data source |
| Notifications | Manager alerts (via CRM workflow) |

---

## Events

`RecommendationGenerated`, `AISalesLeadQualified`, `ConversationSummarized`, `CustomerIntentDetected`, `OfferGenerated`, `FollowUpScheduled`

---

## API — `/api/auto/v1/ai`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/metrics` | AI sales metrics |
| POST | `/agents/dispatch` | Dispatch AI agent |
| GET | `/customers/{id}/intelligence` | Customer intelligence profile |
| GET | `/customers/{id}/intent` | Purchase intent |
| GET | `/customers/{id}/recommendations` | Personalized recommendations |
| GET | `/customers/{id}/recommendations/cross-sell` | Cross-sell |
| GET | `/customers/{id}/recommendations/trade-in` | Trade-in suggestions |
| GET | `/vehicles/{id}/recommendations/alternatives` | Alternative vehicles |
| GET | `/vehicles/{id}/recommendations/accessories` | Accessory recommendations |
| POST | `/recommendations/upsell` | Upsell recommendations |
| GET | `/leads/{id}/intelligence` | Lead intelligence report |
| POST | `/leads/{id}/qualify` | AI qualify lead |
| POST | `/conversations` | Start conversation |
| POST | `/conversations/{id}/turns` | Append turn + suggestion |
| POST | `/conversations/{id}/summarize` | Summarize conversation |
| POST | `/offers` | Generate sales offer |
| POST | `/offers/{id}/negotiate` | Negotiate terms |
| GET | `/knowledge/search` | Search knowledge base |
| POST | `/workflows/onboard` | Customer onboarding workflow |
| POST | `/workflows/follow-up` | Schedule follow-up |

---

## Manifest

`application_version: "1.3.0-alpha"`

---

## Tests

```bash
pytest tests/test_ai_sales_engine.py -q
```

---

## Developer Guide

Access via `auto_marketplace.ai_sales_engine`. Platform Core is never modified — all integration uses application-layer bridges in `ai_sales/integration.py`.

```python
auto_marketplace.ai_sales_engine.metrics()
auto_marketplace.ai_sales_engine.get_agent(AgentType.SALES)
await auto_marketplace.ai_sales_engine.workflow.schedule_test_drive(customer_id, vehicle_id, dealer_id)
```
