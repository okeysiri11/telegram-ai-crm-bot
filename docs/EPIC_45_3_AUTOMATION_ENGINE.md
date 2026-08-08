# EPIC 45.3 — Universal Automation Engine

**Status:** Done · **Version:** 45.3.0 · **Date:** 2026-08-07

## Decision

Extend existing `platform_workflows/` as Universal Automation façade.
Do **not** create a seventh workflow SoR. Graph SoR remains `platform_workflow`.
Execution of AI steps: **Hercules only**. Integrate Mode (45.1) + Memory (45.2).

## Shipped

- Planner · Builder · Orchestrator · Parallel · Retry · Approval · Cost · Scheduler · Runner · Monitor · Library
- API `/api/v1/workflows*`
- Telegram `⚡ Автоматизация`
- Web `/workflows` · `/automation-engine`
- Beauty auto chain
- Docs listed in epic

## Tests

`tests/test_universal_automation_45_3.py` — 700+ cases
