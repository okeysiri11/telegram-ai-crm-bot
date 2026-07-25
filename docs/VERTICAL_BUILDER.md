# Enterprise Vertical Builder

Sprint **28.4** / Platform Builder **v1.3.0**

Visually create complete Enterprise Verticals without programming.

## Module

Platform Builder → Vertical Builder (`/platform-builder/vertical`)

API: `/api/platform-builder/v1/vertical/*`

## Architecture rule

Every created object automatically receives:

- **Logical Representation** — identity, type, attributes (AI Operations ready)
- **Visual Representation** — icon, color, position, city slot (AI City / 3D ready)

Visual consumers: AI Operations Center · AI Team Center · 2D AI City · Future 3D Visualization

## Wizard steps (10)

1. Vertical Information — name, description, industry size, logo, brand color, preview
2. Select Industry — Medical, Beauty, Construction, … Custom (Description / Benefits / Use Cases / Example)
3. Module Selection — CRM, ERP, Finance, Warehouse, Documents, Analytics, Knowledge Base, Automation, Marketplace, Telegram, Mobile, Website, API, Calendar, Notifications, Workflows
4. AI Configuration — connect existing AI Team or launch AI Builder
5. AI Concierge — attach Concierge or create new
6. Dashboard — widgets + live preview
7. Workspace — departments, menus, navigation
8. Live Organization Preview — Owner, Concierge, Departments, AI Team, Connections, Future AI City Position
9. Summary — Vertical Card
10. Create — register Vertical, Modules, Workspace, AI, Concierge, Knowledge, Dashboard, Organization + prepare Visual Layer

## Platform Registry

Create writes into `platform_builder_platform_registry` with dual representations for every object.

## Layout

- Backend: `applications/platform_builder/vertical/`
- Frontend: `src/web/platform-builder/vertical/`
- Knowledge: `knowledge/platform_builder/vertical_builder/`
- Tests: `tests/test_vertical_builder_28_4.py`
