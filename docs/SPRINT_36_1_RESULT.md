# Sprint 36.1 Result — Enterprise Event Bus

## Summary

Shipped Enterprise Event Bus control plane as `platform_enterprise_event_bus/`.

**SoR unchanged:** `events.event_bus.PlatformEventBus`  
**Rejected:** `platform_core/event_bus/` (forbidden package)

## Delivered

- Topics, filters (wildcard/regex/priority/tenant/user), publish/subscribe, broadcast/multicast, delayed delivery
- Event store, replay engine, DLQ, retry manager, signing/validation, audit, metrics
- REST `/api/event-bus` + management dual-prefix + WebSocket `/api/event-bus/ws`
- ORM tables + Alembic `j3d456789012`
- UI at `/platform-builder/event-bus`
- Docs updated in `docs/EVENT_BUS.md`
- Tests `tests/test_event_bus_36_1.py`
- Realtime channel `event_bus`
- Compatible with Sprint 36.0 Service Builder (`svc_event_bus` APIs)

## Success criteria

| Criterion | Status |
|-----------|--------|
| Event Bus operational | ✔ |
| Services communicate through events | ✔ (bridge to PlatformEventBus) |
| Replay | ✔ |
| Dead-letter queue | ✔ |
| Retry engine | ✔ |
| WebSocket live stream | ✔ |
| Monitoring dashboard | ✔ |
| REST API | ✔ |
| Tests | `tests/test_event_bus_36_1.py` |
