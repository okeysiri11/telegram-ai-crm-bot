# Enterprise Service Builder — Sprint 36.0

## Architecture decision

**Rejected:** `platform_core/service_builder/` — the repository forbids a physical `platform_core/` package (composed Core; see `docs/PLATFORM_CORE.md`, `PLATFORM_STANDARDS.md`, TD-62).

**Chosen:** `platform_service_builder/` — canonical `platform_<capability>` package that extends USC foundation (`platform_architecture/service_constructor_foundation.py`, TD-63) without inventing a second discovery bus.

```
Platform (composed Core)
        ↓
platform_service_builder   ← this module (SoR for service install/lifecycle)
        ↓
Providers / AI / Runtimes (Event Bus, Workflow, AI, Multi-Agent, Creative, City)
```

Registered in `platform_architecture/canonical_services.py` as `service_builder`.

---

## Architecture

| Component | Role |
|-----------|------|
| `ServiceRegistry` | In-memory catalog of `ServiceDefinition` + semantic versions |
| `ServiceDefinition` | Runtime record (state, metrics, config, sandbox) |
| `ServiceManifest` | Package metadata (id, version, deps, permissions, healthcheck, …) |
| `ServiceVersion` | Version history with active pointer |
| `ServiceLifecycleManager` | install → load → start/stop/restart/reload/enable/disable/uninstall |
| `ServiceDependencyResolver` | Graph, cycles, startup/shutdown order |
| `ServiceLoader` | Load optional modules without mutating Core |
| `ServiceSandbox` | Isolated per-service runtime context |
| `ServiceHealthChecker` | Heartbeat, CPU/RAM, latency, availability |
| `ServiceConfiguration` | Settings / env / feature flags / resources |
| `ServicePermissionResolver` | API / event / storage / AI tool / integration scopes |
| `ServiceAuditLogger` | Who / when / old→new state / duration / result |
| `ServiceBuilderService` | Facade composing the above |

Foundation catalog seeds six future runtimes: Event Bus, Workflow, AI, Multi-Agent, Creative Factory, Enterprise City.

---

## Lifecycle

```
Draft → Installed → Loaded → Running ⇄ Paused
                 ↘ Failed
                 ↘ Disabled
        Updating / Removing
```

Valid transitions are enforced in `VALID_TRANSITIONS`. Starting a service automatically starts missing dependencies in topological order.

Operations:

- **register** — create draft definition from manifest
- **install** — mark installed (no Core code change)
- **load** — load module + create sandbox
- **start / stop / pause / restart / reload**
- **enable / disable**
- **uninstall** — blocked while dependents are active

---

## Manifest format

```json
{
  "id": "svc_workflow_runtime",
  "name": "workflow_runtime",
  "display_name": "Workflow Runtime",
  "version": "1.0.0",
  "description": "Workflow execution runtime",
  "owner": "platform",
  "category": "workflow",
  "permissions": {
    "allowed_apis": ["workflows.*"],
    "allowed_events": ["workflow.*", "platform.*"],
    "allowed_storage": ["workflows"],
    "allowed_ai_tools": [],
    "allowed_integrations": ["workflow"]
  },
  "dependencies": ["svc_event_bus"],
  "api": ["/workflows", "/workflows/execute"],
  "events": ["workflow.*"],
  "settings": {},
  "healthcheck": {
    "path": "/health",
    "interval_sec": 30,
    "timeout_sec": 5,
    "failure_threshold": 3
  },
  "icon": "git-branch",
  "status": "draft",
  "module_path": null,
  "entrypoint": null
}
```

---

## Dependency system

- Edges: `service → dependencies[]`
- **Startup order:** Kahn topological sort (dependencies first)
- **Shutdown order:** reverse of startup
- **Graph status:** `healthy` | `missing` | `cyclic` | `disabled` | `failed` | `installed`
- Cycles are detected via DFS; cyclic services cannot start

---

## Health system

Each probe records:

- heartbeat timestamp
- response time (ms)
- memory (MB)
- CPU (%)
- errors
- restart count
- availability (%)

`GET /services/{id}/health` probes a single service; `GET /health` returns the fleet monitor.

---

## Permissions

Every service declares:

| Scope | Field |
|-------|-------|
| APIs | `allowed_apis` |
| Events | `allowed_events` |
| Storage | `allowed_storage` |
| AI tools | `allowed_ai_tools` |
| Integrations | `allowed_integrations` |

Supports exact match, prefix `foo.*`, and `*`. Enforcement via `ServicePermissionResolver.require(...)`.

---

## REST API

Primary product prefix: **`/api/service-builder`**

Also registered:

- `/management/v1/service-builder/*`
- `/management/service-builder/*` (legacy, deprecated headers)

| Method | Path | Action |
|--------|------|--------|
| GET | `/services` | List |
| GET | `/services/{id}` | Get |
| POST | `/services` | Register |
| PUT | `/services/{id}` | Update |
| DELETE | `/services/{id}` | Uninstall |
| POST | `/services/{id}/install` | Install |
| POST | `/services/{id}/load` | Load |
| POST | `/services/{id}/start` | Start |
| POST | `/services/{id}/stop` | Stop |
| POST | `/services/{id}/restart` | Restart |
| POST | `/services/{id}/reload` | Reload |
| GET | `/services/{id}/health` | Health |
| GET | `/services/{id}/logs` | Audit logs |
| GET | `/services/{id}/versions` | Versions |
| GET | `/services/{id}/permissions` | Permissions |
| GET | `/services/{id}/dependencies` | Graph |
| GET | `/health` | Fleet health |
| GET | `/dependencies` | Full graphs |

Auth: management JWT / API key (`require_role`).

---

## Database

Alembic revision `i2c345678901` (after `h1b234567890`):

- `service_registry`
- `service_versions`
- `service_dependencies`
- `service_health`
- `service_logs`
- `service_permissions`

ORM: `database/models/service_builder.py` (auto-loaded).

Runtime SoR for Sprint 36.0 is the in-memory facade; tables provide durable persistence for future dual-write.

---

## UI

Routes:

- `/platform-builder/service-builder`
- `/service-builder`

Pages (tabs): Catalog, Installed, Running, Dependencies, Health Monitor, Configuration, Permissions, Logs, Versions.

Service cards show icon, name, version, status, CPU, RAM, uptime, dependencies, owner, last update, and Start/Stop/Restart/Reload/Update/Configure/Logs actions.

---

## Examples

```python
from platform_service_builder import service_builder

service_builder.ensure_seed()
service_builder.start("svc_workflow_runtime")  # starts Event Bus first
print(service_builder.health_of("svc_workflow_runtime"))
print(service_builder.dependency_graph("svc_workflow_runtime"))
print(service_builder.check_permission("svc_ai_runtime", api="ai.invoke"))
```

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/api/service-builder/services

curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/api/service-builder/services/svc_event_bus/start
```

---

## Testing

```bash
.venv/bin/python -m pytest tests/test_service_builder_36_0.py -vv
```

Covers registration, install, start/stop, reload/restart, health, permissions, dependency/version resolvers, REST API, UI presence, ORM tables, canonical registration.

---

## Success criteria

| Criterion | Status |
|-----------|--------|
| Install without Core changes | ✔ |
| Semantic versioning | ✔ |
| Auto dependency resolve | ✔ |
| Health monitoring | ✔ |
| Permissions enforced | ✔ |
| REST API operational | ✔ |
| UI operational | ✔ |
| Audit logging | ✔ |
| Tests | `tests/test_service_builder_36_0.py` |
