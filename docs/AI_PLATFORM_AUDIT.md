# AI Platform Audit — Sprint 30.2

## Inventory

| Capability | Location | Status |
|------------|----------|--------|
| AI Concierge | `platform_builder/concierge`, ecosystem assistant | **I** |
| AI Team Orchestrator | `collaborative_ai`, `ai_team`, hub EAO | **I/P** |
| AI Production | `platform_enterprise_production`, hub EPD | **I/P** |
| AI Marketing | `platform_ai_marketing_os`, hub AMO | **I/P** |
| AI Sales | docs + auto buyer/seller AI APIs | **P** |
| AI Customer Success | Sparse / docs | **A/P** |
| AI Analytics | PB intelligence/experience, hub analytics | **I/P** |
| Knowledge Memory | platform_ai memory, EKP | **I/P** |
| Agent Memory | platform_ai / agents | **P** |
| Agent Communication | collaborative AI, ecosystem communication | **I/P** |
| Agent Registry | AI registry (app ecosystem), platform agents | **I/P** (stubs in places) |
| Agent Permissions | platform_security scopes, RBAC | **P** |
| Agent Routing | `services/ai_router.py`, registries | **P/D** |
| Industry Knowledge | Vertical knowledge + PB knowledge frame | **P** |

## Growth layer validation

| Required layer | Present as platform capability? | Industry-specific fork needed? |
|----------------|----------------------------------|--------------------------------|
| AI Concierge | Yes | **No** — configure per org |
| AI Team Orchestrator | Yes | **No** |
| AI Production Department | Yes (libs/hub) | **No** |
| AI Marketing Department | Yes | **No** |
| AI Sales Department | Partial | **No** — complete as platform binding |
| AI Customer Success | Weak | **No** — add platform module later |
| AI Analytics | Yes | **No** |

## Permissions model (target — extend existing)

- Org-scoped AI teams  
- Role → AI capability mapping via RBAC v2  
- God Mode / platform_owner remains exceptional  
- Users never cross org boundaries  

## Risks

1. Builtin agents marked demo/stub in older audits — treat as non-production until certified.  
2. Telegram AI routes parallel enterprise AI — keep both; don’t merge hastily.  
3. Do not implement “Cafe Concierge Engine” as a fork — extend Concierge with Cafe capabilities.

## Recommendations

1. Publish **AI Growth Layer binding matrix** (org → layers → permissions).  
2. Strengthen Customer Success as platform capability.  
3. Certify agent registry stubs before production AI features.  
4. Wire Identity Center permissions into agent routing.  
