# Platform Builder Core

Sprint **28.1** / Application **v1.0.0** — visual operating system for building platform objects.

## Application

`platform_builder`

## API

`/api/platform-builder/v1`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health + readiness |
| POST | `/bootstrap` | Bootstrap builder core |
| GET | `/inventory` | Catalog inventory |
| GET | `/dashboard` | Builder dashboard |
| GET | `/builders` | List builders |
| GET | `/builders/{id}` | Builder steps + framework |
| POST | `/builders/{id}/preview` | Frame preview |
| POST | `/builders/{id}/create` | Frame create |
| GET/POST | `/academy` | Academy modes / learning toggle |
| GET | `/academy/{id}/guide` | Screen guide |
| GET | `/help/{id}` | Positive help content |
| GET | `/menu` | Role-aware menu (hides God Mode) |
| GET | `/roles` | Includes Platform Owner |
| GET | `/god-mode` | Owner-only diagnostics |
| POST | `/god-mode/action` | Owner-only actions |

## Main menu

Platform Builder → Dashboard, Vertical, AI, Concierge, CRM, ERP, Workflow, Knowledge, Automation, Dashboard Builder, Template, Marketplace, Builder Academy, God Mode (Platform Owner only).

## Builder Framework

Every builder inherits:

**Step → Explanation → Information → Example → Preview → Create**

## Builder Academy

- Quick Start
- Guided Learning (explains every screen)
- Expert Mode

Learning mode can be enabled/disabled per builder.

## Help System

Positive guidance only: Purpose, Benefits, Typical use, Business value — plus short description, detailed explanation, example, popup, tooltips.

## God Mode

Isolated Platform Owner surface for editing any platform object, diagnostics, architecture, developer console, version history, and rollback.

## Layout

- Backend: `applications/platform_builder/`
- Frontend: `src/web/platform-builder/`
- Knowledge: `knowledge/platform_builder/`
