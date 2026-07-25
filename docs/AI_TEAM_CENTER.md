# AI Team Center

Sprint **28.3** / Platform Builder **v1.2.0**

Dashboard for all **AI Specialists** in an organization. Created with the Concierge and managed by the Concierge.

## Rules

- Unlimited AI Specialists
- Concierge manages Specialists
- Specialists execute work
- One Concierge per organization (see [AI Concierge](./AI_CONCIERGE.md))

## Module

Platform Builder → AI Team Center (`/platform-builder/ai-team`)

API: `/api/platform-builder/v1/ai-team/*`

## AI Card fields

- Name, Avatar, Profession, Specialization
- Status, Current Task, Memory Usage, Last Activity, Capabilities

## Owner actions

Open Chat · Assign Task · View Knowledge · View Memory · Pause Agent · Resume Agent · Edit Agent · Replace Agent · Remove Agent

## Group AI Chat Foundation

Architecture only. Owner starts a conversation and invites Lawyer, Accountant, Marketing, HR, Medical, Finance, Analytics, or Custom Specialists. Model includes conversation history, participant list, speaking order, AI summary, and decision summary.

## Layout

- Backend: `applications/platform_builder/ai_team/`
- Frontend: `src/web/platform-builder/ai-team/`
- Knowledge: `knowledge/platform_builder/ai_team/`
- Tests: `tests/test_ai_team_center_28_3.py`
