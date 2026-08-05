# Production Center

**Sprint:** 27.9 / 28.2 Runtime / **28.3 AI Studio shared store** · Route `/production-studio`

## Purpose

Professional creative studio as a **navigation + orchestration** surface on the Enterprise OS. Capability owner for studios, prompts, media, projects, and generation history shared with `/ai-studio`.

## Sections

| Tab | Capability |
|-----|------------|
| Studios | 17 studio cards · StudioWorkbench |
| Projects | Explorer · dashboard · gallery |
| Pipeline | Builder · stage advance · multi-agent chains |
| **Runtime** | Queues · workers · universal pipelines |
| Prompts | Collections · categories · variables · versioning |
| Media | Library browser |
| History | Generation history · favorites |
| Automation | Batch · queue · schedule · retry → Job Manager |

## Deep links

- `?studio=reels` — open studio workbench  
- `?tab=pipeline|runtime|prompts|media|projects|history|automation`  

## Runtime rule

Execution goes through **Enterprise Runtime** (`productionRuntime` → Job Manager). Visual AI UX also available at `/ai-studio` (Sprint 28.3) using the same store.

## Linked modules

AI Studio · Workflow Center · AI Runtime · AI Builder · Concierge · Themes · Assets · Documents · Analytics · Desktop · Enterprise City

## Persistence

`localStorage` key `ews_ai_production_v1` (snapshot **v2** — migrates from v1)
