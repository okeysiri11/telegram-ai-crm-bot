# Event System Certification

> Generated: 2026-07-19 12:58:24 UTC

## Verdict: **PASS**

## Canonical Bus

- **PlatformEventBus** (`events/event_bus.py`) — canonical in-process bus
- **events/publisher.py** — unified publish entry

## Adapters

- CRM Outbox (`services/crm_event_bus.py`) — persists after `publish_crm_to_platform_bus`
- Legacy EventBus — re-exported via `platform_legacy` in `events/__init__.py`

- CRM adapter wired to PlatformEventBus: **unknown**
- Direct legacy publishers in pg engines: **0**

## Direct CRM Publishers (must migrate to events/publisher)

