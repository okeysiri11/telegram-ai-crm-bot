# Collaborative AI

Sprint **28.8** / Platform Builder **v1.7.0** / Collaborative AI **1.0**

Multiple AI Specialists work together as one coordinated organization. The AI Concierge orchestrates discussions, delegates work, combines results, and delivers a unified answer.

## Module

Platform Builder → Collaborative AI (`/platform-builder/collaborative-ai`)

API: `/api/platform-builder/v1/collaborative-ai/*`

## Flow

1. **AI Team Creation** — Specialists · Concierge · Team Name · Business Goal · Priority
2. **Role Assignment** — Role · Responsibilities · Priority · Permissions · Knowledge Scope · Expected Output
3. **Collaborative Session** — Participants · Current Speaker · Current Task · Discussion Progress · Consensus Status
4. **Task Distribution** — Concierge assigns, balances, coordinates, collects
5. **Shared Knowledge** — Context · References · Findings · Shared conclusions
6. **Decision Engine** — Alternatives · Pros · Cons · Risk Notes · Recommended Decision · Business Impact
7. **Executive Summary** — Final Report · Decision Explanation · Action Plan
8. **Team Performance** — Tasks · Response Time · Collaboration Quality · Knowledge Usage · Contribution
9. **Explain Decision** — Why · Benefits · Alternatives · Expected Result
10. **AI Ops Foundation** — Team Map · Visual Layer · Visual IDs · Live Organization · 2D AI City
11. **Create** — Register AI Team · Collaborative Session · Decision Engine · Knowledge Exchange

## Layout

- Backend: `applications/platform_builder/collaborative_ai/`
- Frontend: `src/web/platform-builder/collaborative-ai/`
- Knowledge: `knowledge/platform_builder/collaborative_ai/`
- Related: [ENTERPRISE_COLLECTIVE_INTELLIGENCE.md](./ENTERPRISE_COLLECTIVE_INTELLIGENCE.md)
- Tests: `tests/test_collaborative_ai_28_8.py`
