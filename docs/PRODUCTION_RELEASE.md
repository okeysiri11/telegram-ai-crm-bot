# Auto Marketplace — Production Release 2.0.0

> Sprint 6.8 — production deployment, validation, and go-live readiness

## Release Summary

| Field | Value |
|-------|-------|
| Application Version | **2.0.0** |
| Release Status | **Production Ready** |
| Platform Dependency | **AI Platform Core v3.0** |

---

## Go-Live Checklist

1. Run production validation: `GET /api/auto/v1/ops/release/report`
2. Verify version: `GET /api/auto/v1/ops/deployment/preflight?version=2.0.0`
3. Create backup: `POST /api/auto/v1/ops/backups`
4. Deploy and verify health: `GET /api/auto/v1/ops/health`
5. Verify readiness: `GET /api/auto/v1/ops/ready`
6. Enable monitoring: `GET /api/auto/v1/ops/observability`
7. Disable maintenance mode: `POST /api/auto/v1/ops/maintenance/disable`

Full checklist: `GET /api/auto/v1/ops/deployment/checklist`

---

## Production Validation

```python
from applications.auto_marketplace import auto_marketplace

report = await auto_marketplace.production_engine.generate_release_report()
assert report.production_ready
```

Validates: modules, API, AI integrations, security, workflows, migrations, disaster recovery.

---

## Operations Guide

| Probe | Endpoint |
|-------|----------|
| Health | `GET /api/auto/v1/ops/health` |
| Readiness | `GET /api/auto/v1/ops/ready` |
| Liveness | `GET /api/auto/v1/ops/live` |
| Metrics | `GET /api/auto/v1/ops/metrics` |

Maintenance: `POST /api/auto/v1/ops/maintenance/enable|disable`  
Rollback: `GET /api/auto/v1/ops/deployment/rollback`

---

## Disaster Recovery

- **RTO:** 30 minutes | **RPO:** 15 minutes | **Retention:** 30 days
- Backup: `POST /api/auto/v1/ops/backups`
- Procedures: `GET /api/auto/v1/ops/backups/procedures`

---

## Support

- Admin guide: `GET /api/auto/v1/ops/guides/admin`
- User guide: `GET /api/auto/v1/ops/guides/user`
- Incidents: `GET /api/auto/v1/ops/incidents`

---

## Tests

```bash
pytest tests/test_production_release.py -q
```

---

## Release Artifacts

- `applications/auto_marketplace/release/manifest.json`
- `applications/auto_marketplace/release/RELEASE_NOTES.md`
- `applications/auto_marketplace/manifest.json`
