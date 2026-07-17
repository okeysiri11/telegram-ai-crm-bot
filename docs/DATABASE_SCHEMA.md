# Database Schema

PostgreSQL database accessed via SQLAlchemy 2 async (`asyncpg`).

## Connection

| Setting | Default |
|---------|---------|
| URL env | `DATABASE_URL` |
| Default URL | `postgresql+asyncpg://postgres:postgres@localhost:5432/ai_ecosystem` |
| Session helper | `database/session.py` → `get_session()` |
| Migrations | Alembic in `migrations/versions/` |

## Layer responsibilities

| Layer | Location | Responsibility |
|-------|----------|----------------|
| Models | `database/models/` | ORM entities, indexes, enums |
| Repositories | `repositories/` | Queries, CRUD — no business rules |
| Services | `services/pg_*` | Transactions, validation, side effects |

**Rule:** only services and repositories call `get_session()`.

## Core entity groups

### Users and permissions

| Model | Table | Purpose |
|-------|-------|---------|
| `User` | `users` | Telegram users |
| `Role` | `roles` | Legacy roles |
| `RbacRole` | `rbac_roles` | RBAC v2 |
| Permission engine | `permission_engine_*` | Live permission system |

### Client requests

| Model | Table | Purpose |
|-------|-------|---------|
| `AutoClientRequest` | `auto_client_requests_v1` | Auto vertical client requests |
| `ClientRequest` | `client_requests` | Unified CRM requests |
| `LeadEngineLead` | `lead_engine_leads_v1` | Multi-vertical leads |

### Automotive

| Model | Table | Purpose |
|-------|-------|---------|
| `Car` | `cars` | Vehicle inventory |
| `VinReport` | `vin_reports_v1` | VIN decode history |
| `AutomotiveInventory` | various | Marketplace inventory |
| Partner/dealer models | `automotive_*`, `dealer_*` | Partners, onboarding, treasury |

### CRM pipeline

| Model | Purpose |
|-------|---------|
| `CrmPipelineStage` | Kanban stages per vertical |
| `CrmPipelineLead` | Lead cards on board |
| `CrmPipelineDeal` | Deal cards on board |
| `CrmPipelineTransition` | Stage move audit |

Verticals on pipeline: `auto`, `agro` (see `CRM_PIPELINE_VERTICALS`).

### Payments and billing

| Model | Purpose |
|-------|---------|
| `PaymentEngineV1*` | Manual payment verification |
| `CommercialBilling*` | Subscription plans |
| `CartEngineV1*` | Cart and orders |

### Multi-tenant

| Model | Purpose |
|-------|---------|
| `PartnerTenant` | Tenant isolation |
| `TenantUserRole` | User-tenant role bindings |

## Repository pattern

```python
from repositories.client_request_repository import ClientRequestRepository

async with get_session() as session:
    repo = ClientRequestRepository(session)
    row = await repo.get_by_number("AUTO-0001")
```

Base class: `src/platform/layers/base_repository.py`

## Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

Model registration: `database/migration_models.py` → `load_all_models()`

## Legacy SQLite

`database_legacy.py` — **deprecated**. Do not add new features. Existing imports in `handlers.py` migrate incrementally to PostgreSQL repositories.

## Conventions

- Table suffix `_v1` for versioned engines
- UUID primary keys via `UUIDPrimaryKeyMixin`
- Timestamps via `TimestampMixin`
- JSONB for flexible metadata fields
- Indexes on foreign keys and status columns

See also [database.md](database.md) for naming conventions.
