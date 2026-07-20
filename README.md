# TelegramBotCourse — BIDEX Platform v1.0

Enterprise CRM platform with Telegram bot integration, PostgreSQL persistence, and a governed multi-layer architecture.

## Platform overview

| Layer | Path | Role |
|-------|------|------|
| Management API | `platform_management/` | Authenticated admin REST at `/management/v1` |
| Public API | `platform_api/`, `api/` | Frozen public contract at `/api/v1` |
| Architecture governance | `platform_architecture/` | Executable rules, dependency graph, CI validation |
| Plugin SDK | `platform_plugin_sdk/` | Extension surface for plugins |
| Platform SDK | `platform_sdk/` | Vertical registration and workflow integration |
| Event system | `events/` | **PlatformEventBus** — canonical in-process event routing |
| Services | `services/` | Business logic (no direct HTTP exposure) |
| Repositories | `repositories/` | PostgreSQL data access |
| Certification | `platform_certification/` | Sprint 1.5 release gates |
| Platform Memory | `platform_memory/` | AI Memory & Context Engine (Sprint 2.1–2.2) |
| Multi-Agent Orchestrator | `platform_orchestrator/` | Central AI agent execution layer (Sprint 2.3) |
| Agent Registry | `platform_agents/` | Plugin-based AI agent registry (Sprint 3.1) |
| Workflow & Task Engine | `platform_workflow/` | Enterprise workflow execution (Sprint 3.2) |
| Tool Framework | `platform_tools/` | Universal tool & integration framework (Sprint 3.3) |
| Reasoning Engine | `platform_reasoning/` | AI reasoning & intelligence layer (Sprint 4.1) |
| Planning Engine | `platform_planning/` | Goal-oriented execution planning (Sprint 4.2) |
| Decision Engine | `platform_decision/` | Adaptive execution strategy selection (Sprint 4.3) |
| Learning Engine | `platform_learning/` | Continuous improvement from feedback (Sprint 4.4) |
| Collaboration Engine | `platform_collaboration/` | Multi-agent coordination & consensus (Sprint 4.5) |
| Security Layer | `platform_security/` | Enterprise auth, RBAC, secrets & audit (Sprint 5.1) |
| Observability Layer | `platform_observability/` | Logging, tracing, metrics & diagnostics (Sprint 5.2) |
| Reliability Layer | `platform_reliability/` | Fault tolerance, recovery & failover (Sprint 5.3) |
| Configuration Layer | `platform_configuration/` | Centralized config, deployment & feature flags (Sprint 5.4) |
| Validation Layer | `platform_validation/` | Production readiness & QA certification (Sprint 5.5) |
| Auto Marketplace | `applications/auto_marketplace/` | Production app — catalog, CRM, AI sales (Sprint 6.1–6.4) |

## Project structure

```
TelegramBotCourse/
├── applications/              # Production apps on Platform Core v3.0
│   └── auto_marketplace/      # AI Auto Marketplace (Sprint 6.1–6.2)
├── startup.py                 # Production entry (bot + API server)
├── api/server.py              # HTTP app factory
├── platform_management/       # /management/v1 authenticated API
├── platform_memory/           # Semantic AI memory & context engine
├── platform_orchestrator/     # Multi-agent orchestration engine
├── platform_agents/           # Plugin-based agent registry
├── platform_workflow/           # Workflow & task engine
├── platform_tools/              # Tool & integration framework
├── platform_reasoning/          # AI reasoning engine
├── platform_planning/           # AI planning engine
├── platform_decision/           # AI decision engine
├── platform_learning/           # AI learning & feedback engine
├── platform_collaboration/      # Multi-agent collaboration engine
├── platform_security/           # Enterprise security layer
├── platform_observability/      # Logging, tracing, metrics & diagnostics
├── platform_reliability/        # Fault tolerance, recovery & failover
├── platform_configuration/    # Configuration center + deployment layer (Sprint 5.4)
├── platform_validation/       # Validation & production readiness (Sprint 5.5)
├── platform_architecture/     # Governance validators
├── platform_plugin_sdk/       # Plugin extension SDK
├── events/                    # PlatformEventBus + CRM publisher
├── services/                  # Domain services
├── repositories/              # Data access
├── tests/                     # Regression + security suites
├── scripts/
│   ├── validate_architecture.py
│   ├── validate_legacy_migration.py
│   └── run_platform_certification.py
└── .github/workflows/architecture.yml
```

## Setup

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment (`.env`):

   ```
   BOT_TOKEN=your_telegram_bot_token
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
   POSTGRES_ONLY=true
   ```

4. Run the platform:

   ```bash
   python startup.py
   ```

## Validation

```bash
.venv/bin/python -m pytest tests/ -q -m "not slow"
.venv/bin/python scripts/validate_architecture.py
.venv/bin/python scripts/validate_legacy_migration.py
.venv/bin/python scripts/generate_architecture_baseline.py
.venv/bin/python scripts/run_platform_certification.py
```

**Release candidate:** `platform-core-v1.0.0-rc1` — frozen Platform Core baseline (Sprint 1.5).

## API surfaces

- **Management (authenticated):** `/management/v1/*` — configuration, verticals, workflows, SLA, managers
- **Public (versioned):** `/api/v1/*` — frozen marketplace REST contract
- **Legacy admin routes removed:** former unauthenticated `/api/v1/admin/*` registrations are not mounted; use `/management/v1`

## Requirements

- Python 3.10+
- PostgreSQL (production)
- See `requirements.txt` for Python packages

## Documentation

- `docs/PLATFORM_CERTIFICATION.md` — certification report
- `docs/ARCHITECTURE_BASELINE.md` — frozen RC1 architecture baseline
- `docs/architecture_baseline/` — module, dependency, service, import graphs
- `ARCHITECTURE_REPORT.md` — governance audit output
- `docs/architecture/PLATFORM_MEMORY.md` — memory engine architecture (Sprint 2.1)
- `docs/architecture/SEMANTIC_MEMORY_REPORT.md` — semantic memory report (Sprint 2.2)
- `docs/architecture/ORCHESTRATOR.md` — multi-agent orchestrator (Sprint 2.3)
- `docs/architecture/ORCHESTRATOR_REPORT.md` — orchestrator architecture report (Sprint 2.3)
- `docs/AGENT_REGISTRY.md` — agent registry & plugin SDK guide (Sprint 3.1)
- `docs/WORKFLOW_ENGINE.md` — workflow & task engine (Sprint 3.2)
- `docs/TOOLS.md` — tool & integration framework (Sprint 3.3)
- `docs/REASONING.md` — reasoning engine (Sprint 4.1)
- `docs/PLANNING.md` — planning engine (Sprint 4.2)
