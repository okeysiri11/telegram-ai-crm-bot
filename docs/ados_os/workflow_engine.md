# Workflow Engine 2.0 (Collaboration)

Kernel `src/kernel/workflow` provides graph execution (sequential, parallel, retry, pause/resume/cancel, history).

Multi-agent collaboration runs through `CollaborationEngine` (`src/orchestrator/collaboration`):

- Templates → steps → agents via **AI Orchestrator only**
- Shared context, timeline, priority queue
- REST: `POST /workflow/start`, `GET /workflow/:id`, `GET /workflow/history`, pause/resume/cancel

See also: `knowledge/ados_os/` and Control Center **Workflows** page.
