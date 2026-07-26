# AI Team Collaboration & Multi-Agent Workspace — Sprint 32.6

Platform Builder **v1.52.0** · Sprint **32.6**

## Goal

Пользователь ощущает работу с целой AI-командой, а не с одним ассистентом — без новых Engine / Concierge / Workspace Engine / Store.

## Constraints

- **No new AI Engine**
- **No new Concierge**
- **No new Workspace Engine**
- **No new Store**
- Reuse: AI Core, Concierge, AI Team Center, Workspace Engine, Dashboard, Mission Control, Enterprise Intelligence, Knowledge Base, Notification Center, live-ops shared snapshot, First Entry

## Delivered

1. **AI Team Workspace** — Concierge + specialists, status, task, last activity, load  
2. **Task Distribution** — Marketing / Sales / Legal / Analytics / Ops  
3. **AI Collaboration Timeline** — Concierge → specialists → Result  
4. **Team Health** — active, done, errors, queue, avg time  
5. **AI Conversation** — journal from AI events + notifications (no Chat Engine)  
6. **Knowledge Contribution** — who updated / created / used KB  
7. **Executive Overview** — compact daily team summary  
8. **Performance** — pure derive + shared `useLiveEnterprise`

## Mount

- Full workspace on `/platform-builder/ai-team` (`AITeamCenterPage`) — enriches with existing AI Team API members when loaded  
- Compact strip in `FullLayout`

## Architecture note

`src/web/src/ai-team-collaboration/` — presentational derive layer over existing providers/context.
