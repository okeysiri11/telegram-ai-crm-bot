# Port Enterprise Deployment

**Version:** `4.6.0-enterprise`  
**Sprint:** 15.8

## Steps

1. Apply `applications/port_enterprise/release/config.template.env`
2. Register routes with `register_port_enterprise_routes`
3. Confirm `/api/port-enterprise/v1/health`
4. Bootstrap certification `/api/port-enterprise-certification/v1/bootstrap`
5. Verify all module healthchecks from `DEPLOYMENT_MANIFEST.json`

## Artifacts

See `applications/port_enterprise/release/` for manifests, checklist, installation, admin, and operations guides.
