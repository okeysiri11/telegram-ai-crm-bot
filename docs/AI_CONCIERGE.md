# Enterprise AI Concierge

Sprint **28.3** / Platform Builder **v1.2.0**

AI Concierge is **not** an AI Agent. It is the central intelligence of an organization.

## Rules

- Exactly **one Concierge per Organization**
- Independent from AI Agents
- Concierge coordinates Specialists
- Specialists execute work

## Module

Platform Builder → Concierge Builder (`/platform-builder/concierge`)

API: `/api/platform-builder/v1/concierge/*`

## Wizard steps

1. Concierge Identity — name, avatar, gender, voice, communication style + live preview
2. Concierge Role — Executive Assistant, Business Concierge, …
3. Organization Access — CRM, ERP, Documents, AI Registry, …
4. AI Orchestration — delegate, call, monitor, coordinate, …
5. Proactive Assistance — morning briefing, digests, reminders, …
6. Owner Relationship — only when requested → daily strategic advisor
7. Smart Recommendations — architecture only
8. Summary — Concierge Card
9. Create — register, link organization, Concierge Registry

## Layout

- Backend: `applications/platform_builder/concierge/`
- Frontend: `src/web/platform-builder/concierge/`
- Knowledge: `knowledge/platform_builder/concierge/`
- Tests: `tests/test_ai_concierge_28_3.py`
