# Platform Standards

**Sprint:** 32.2 · Applies to new and extended Platform Core code.

## Naming

| Kind | Convention | Example |
|---|---|---|
| Platform packages | `platform_<capability>` | `platform_workflow` |
| Enterprise additive | `platform_enterprise_<capability>` | `platform_enterprise_ai_provider_hub` |
| Vertical apps | `applications/<vertical>_…` | `applications/auto_marketplace` |
| Services | `*_engine.py` / `*_service.py` | `pricing_engine.py` |
| Facades / foundations | `*_foundation.py` | `pricing_foundation.py` |
| Events | prefer `PlatformEventBus` | never a new top-level `*EventBus` SoR |
| Docs | `SCREAMING_SNAKE.md` under `docs/` | `PLATFORM_CORE.md` |

Do **not** introduce a package named `platform_core` — Core is composed.

## Folder structure (repo)

```
events/                 # Event Bus SoR
services/               # Core + shared business services
repositories/           # Postgres access
database/               # models, session, migrations
platform_<capability>/  # capability modules
platform_architecture/  # governance only
applications/<vertical>/  # vertical only
api/                    # HTTP mount
src/web/                # Enterprise Web
```

## Module structure (capability package)

```
platform_example/
  __init__.py
  service.py | engine.py
  models.py | schemas.py   # optional DTOs
  api.py | router.py       # optional HTTP
  README.md                # optional
```

## Layers

| Layer | Responsibility | Must not |
|---|---|---|
| **Domain** | Entities, invariants | Import HTTP / UI |
| **Service** | Use-cases, orchestration | Own SQLAlchemy sessions long-term (prefer repositories) |
| **Repository** | Persistence | Business rules |
| **Presentation** | Web / Telegram UI | Duplicate Core engines |
| **API** | REST DTOs, versioning | Break frozen `/api/v1` without version |
| **AI** | Agents, providers, runtime | Business logic in providers |
| **Workflow** | Definitions + execution | Parallel SoR engines without inventory entry |

## Universal Service Constructor (foundation)

Blueprints compose: Service · Package · Workflow · Pricing · AI · Documents · CRM · Marketplace.  
No UI in foundation sprint — see `platform_architecture/service_constructor_foundation.py`.

## Pricing

- SoR: `services/pricing_engine.py`
- Design surface: `services/pricing_foundation.py` (tariffs, discounts, taxes, commissions, multi-currency, crypto, AI units)

## Enforcement

Standards are enforced by review + `scripts/architecture_sprint_review.py` + `validate_architecture.py`.
