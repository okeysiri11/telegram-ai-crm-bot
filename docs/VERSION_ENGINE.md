# Platform Version Engine

**Sprint:** 34.2D · **Module:** `platform_state.version_engine.VersionEngine`  
**SQLAlchemy primitive:** `database.models.mixins.VersionMixin` (TD-54)

---

## Guarantees

1. Every shared entity mutation goes through `VersionEngine` (or SyncEngine → version bump via adapters).
2. Optimistic locking via `expected_version`.
3. Full revision history + snapshots per version.
4. `compare(left, right)` and `rollback(to_version)`.
5. No client may invent a parallel version counter.

---

## Canonical entity fields

`id`, `version`, `created_at`, `updated_at`, `created_by`, `updated_by`,  
`workspace_id`, `tenant_id`, `source_client`, `change_id`, `deleted_at`, `metadata`, `data`

---

## API

```python
from platform_state.version_engine import version_engine

ent = version_engine.create(entity_type="lead", data={"name": "Acme"}, source_client="web")
ent = version_engine.update(entity_type="lead", entity_id=ent.id, data={"name": "Acme2"}, expected_version=1)
version_engine.history("lead", ent.id)
version_engine.compare("lead", ent.id, 1, 2)
version_engine.rollback(entity_type="lead", entity_id=ent.id, to_version=1)
```

Adapter path uses `bump_compat(..., persist_event=False)` so durable logging stays on SyncEngine → Event Store.
