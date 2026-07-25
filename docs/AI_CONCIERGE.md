# Enterprise AI Concierge

Sprint **28.3** / Platform Builder **v1.2.0**

AI Concierge is **not** an AI Agent. It is the central intelligence of an organization.

## Rules

- Exactly **one Concierge per Organization**
- **Unlimited** AI Specialists
- Concierge manages Specialists
- Specialists execute work
- Independent from AI Agents

## Module

Platform Builder → Concierge Builder (`/platform-builder/concierge`)

API: `/api/platform-builder/v1/concierge/*`

Related: [AI Team Center](./AI_TEAM_CENTER.md)

## Wizard steps (11)

1. Concierge Identity — name, avatar, gender, voice, communication style + live preview
2. Concierge Role — Executive Assistant, Business Concierge, Personal Concierge, Operations Manager, Business Advisor, CEO Assistant, Custom (Purpose / Benefits / Example)
3. Organization Access — CRM, ERP, Documents, Knowledge, AI Registry, Workflow Engine, Analytics, Calendar, Tasks, Marketplace, Notifications, Automation, Dashboards, Departments
4. AI Team Center — specialist dashboard preview and owner actions
5. AI Orchestration — Delegate Tasks, Invite Specialists, Coordinate Team, Summarize Discussions, Recommend Specialists, Create Executive Reports, Prepare Meetings, Monitor AI Team
6. Proactive Assistance — Morning Briefing, Evening Summary, Business Insights, Reminders, Meetings, Highlights, Performance, Daily Digest, Opportunity Detection
7. Owner Relationship — Only When Asked → Daily Strategic Advisor
8. Smart Recommendation Engine — architecture only
9. Group AI Chat Foundation — architecture only (invite roles, history, speaking order, summaries)
10. Summary — Concierge Card, Organization Overview, AI Team Overview
11. Create — Register Concierge, AI Team Center, Organization Connection in Concierge Registry

## Layout

- Backend: `applications/platform_builder/concierge/`
- Frontend: `src/web/platform-builder/concierge/`
- Knowledge: `knowledge/platform_builder/concierge/`
- Tests: `tests/test_ai_concierge_28_3.py`
