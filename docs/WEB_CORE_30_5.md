# Web Core Integration & First Pilot Readiness — Sprint 30.5

**Version:** Platform Builder **v1.30.0** · Sprint **30.5** · **Web Core Integration**  
**Rule:** Connect existing services — no architecture redesign, no new platform branches.

## Mission

Connect backend services with the Web layer and prepare the first internal pilot.

## Deliverables

| Artifact | Path |
|----------|------|
| Web Integration Guide | [WEB_INTEGRATION_GUIDE_30_5.md](./WEB_INTEGRATION_GUIDE_30_5.md) |
| Module Registry | [MODULE_REGISTRY_30_5.md](./MODULE_REGISTRY_30_5.md) |
| Routing Documentation | [ROUTING_30_5.md](./ROUTING_30_5.md) |
| Pilot Guide | [PILOT_GUIDE_30_5.md](./PILOT_GUIDE_30_5.md) |
| Deployment Guide | [DEPLOYMENT_GUIDE_30_5.md](./DEPLOYMENT_GUIDE_30_5.md) |
| Architecture Inventory Update | [ARCHITECTURE_INVENTORY_30_5.md](./ARCHITECTURE_INVENTORY_30_5.md) |
| Technical Debt Status | [TECHNICAL_DEBT_30_5.md](./TECHNICAL_DEBT_30_5.md) |
| Production Readiness Report | [PRODUCTION_READINESS_30_5.md](./PRODUCTION_READINESS_30_5.md) |
| Backlog | [IMPLEMENTATION_BACKLOG_30_5.md](./IMPLEMENTATION_BACKLOG_30_5.md) |

## Demonstrable in Web UI

| Surface | Route |
|---------|-------|
| Pilot Dashboard | `/pilot` |
| Mission Control live panel | `/platform-builder/mission-control` |
| Ecosystem modules | `/workspace/{auto\|beauty\|cafe\|agro\|drone\|legal\|crypto}` |
| Portals | `/portals/*` |

## Sprint result

Shared Web Core complete. Central Module Registry operational. Mission Control connected to live module/OBS status. Business modules load through the shared shell. Centralized logging/telemetry extended. Pilot Dashboard ready for first internal pilot.

Architecture unchanged. Readiness higher than Sprint 30.4.

## Next

Automotive live data workflows on existing shells (not architecture expansion).
