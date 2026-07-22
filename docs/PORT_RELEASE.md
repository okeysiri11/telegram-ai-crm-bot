# Port ERP — Production Release (Sprint 9.8)

Commercial production release for **Port ERP 2.0.0**.

| Field | Value |
|-------|-------|
| Application version | `2.0.0` |
| Enterprise engine | `1.0` |
| Global network | `1.0` |
| API | `/api/port/v1/production` |

## Production Capabilities

- Health monitoring
- Readiness scoring
- Configuration validation
- Dependency validation (platform + ecosystem bridges, manifest)
- Performance benchmark
- Release verification
- Deployment profiles

## Release Gate

Ready when:

1. `application_version == "2.0.0"`
2. Configuration checks pass (`enterprise_engine`, `global_network`, dependencies)
3. Platform / Ecosystem bridges report expected dependency strings
4. Manifest version is `2.0.0`
5. Health probe is healthy
6. Store benchmark under threshold

## Modules

`production/` · `deployment/` · `health/`

```python
from applications.port_erp import port_erp

ready = port_erp.enterprise.production.readiness()
assert ready["application_version"] == "2.0.0"
report = port_erp.enterprise.production.verify_release()
assert report.ready is True
```
