# AI Skills & SDK — Sprint 36.8

## Architecture decision

**Canonical SoR:** `platform_ai` (extends existing `platform_ai/skills`).  
**Rejected:** new `platform_skills` / `platform_core/` package.

Sprint 36.8 productizes **Enterprise AI Skills & SDK** on top of the existing skills framework:

| Layer | Module |
|-------|--------|
| Existing SoR | `platform_ai/skills/*` (registry, manager, executor) |
| Product models | `skills_sdk_models.py` |
| Engine | `skills_sdk_engine.py` |
| Facade | `skills_sdk_service.py` |
| HTTP | `skills_sdk_router.py` |

```
Developer / AI Agent / Voice / Multi-Agent
                ↓
         SkillsSdkService
                ↓
   register → marketplace → install → sandbox execute
                ↓
      Python · TypeScript · REST · MCP SDKs
```

---

## Skills Registry

Categories · versions · permissions · dependencies · cryptographic signatures (`sign_skill`)

## Skill Runtime

Install / uninstall / enable / disable · sandbox execution · resource limits (cpu/memory/timeout) · auto-install for agents

## SDKs

| SDK | Template |
|-----|----------|
| Python | `tpl_python` — `AISkill` subclass |
| TypeScript | `tpl_ts` — fetch client |
| REST | `tpl_rest` — OpenAPI snippet |
| MCP | `tpl_mcp` — `skills.execute` tool |

## Marketplace

Local · enterprise · private · public repositories · updates · ratings · changelog

## REST API

| Prefix | Purpose |
|--------|---------|
| `/api/skills/*` | Lifecycle + execute + marketplace |
| `/api/sdk/*` | Manifest + templates |
| `/management/v1/skills/*` | Management dual-prefix |

## Database (Alembic `r1l234567890`)

`skills` · `skill_versions` · `skill_dependencies` · `skill_permissions` · `installed_skills` · `skill_statistics` · `skill_marketplace`

## UI

`/platform-builder/skills`

Pages: Skills Dashboard · Marketplace · Installed Skills · SDK Explorer · Templates · Version Manager

## Integrations

AI Runtime · Multi-Agent Runtime · Project Memory · Context Engine · Workflow Runtime · Voice Command Center · Service Builder (`svc_skills_sdk`)
