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

## Project structure

```
TelegramBotCourse/
├── startup.py                 # Production entry (bot + API server)
├── api/server.py              # HTTP app factory
├── platform_management/       # /management/v1 authenticated API
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
pytest tests/ -q
python scripts/validate_architecture.py
python scripts/validate_legacy_migration.py
python scripts/run_platform_certification.py
```

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
- `ARCHITECTURE_REPORT.md` — governance audit output
- `platform_manifest.json` — machine-readable platform manifest
