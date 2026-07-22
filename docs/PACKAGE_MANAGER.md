# Package Manager

Install, update, rollback, dependency resolution, compatibility checks, and license issuance.

## API

```http
POST /api/marketplace/v1/packages
{"action":"install","package_id":"..."}

POST /api/marketplace/v1/packages
{"action":"update","installation_id":"...","to_version":"1.1.0"}

POST /api/marketplace/v1/packages
{"action":"rollback","installation_id":"..."}

POST /api/marketplace/v1/packages
{"action":"compatibility","package_id":"...","platform_version":"3.0.0"}
```
