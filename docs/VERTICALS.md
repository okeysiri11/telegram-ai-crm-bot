# Verticals

## Supported verticals

| Code | Maturity | Manager | Service entry |
|------|----------|---------|---------------|
| `auto` | production | Boroda_0003 | `RequestService.create_request(vertical="auto", ...)` |
| `agro` | partial | Christopher Moltisanti | `RequestService.create_request(vertical="agro", ...)` |
| `realty` | scaffold | — | `RequestService.create_request(vertical="realty", ...)` |
| `legal` | scaffold | — | `RequestService.create_request(vertical="legal", ...)` |
| `logistics` | scaffold | — | `RequestService.create_request(vertical="logistics", ...)` |

## Request creation (unified)

```python
from services.request_service import request_service

result = await request_service.create_request(
    vertical="agro",
    client_telegram_id=user_id,
    client_name="Client Name",
    product="Пшеница",
    description="500 т, Odessa",
)
# result["request_number"] → "AGRO-00001"
```

AUTO vertical delegates to `AutoClientRequestEngineV1.submit()`.

## Manager routing

```python
from services.manager_service import manager_service

mgr = await manager_service.resolve_manager_for_vertical("agro")
# Christopher Moltisanti — not SUPER_ADMIN
```

AGRO products (grain, rapeseed, soy, apples, freight, export, import, logistics) all route to AGRO manager.

## Adding a new vertical

1. Add to `RequestService.SUPPORTED_VERTICALS` and `VERTICAL_PREFIX`
2. Add `VerticalDefinition` in `src/verticals/__init__.py`
3. Configure `ManagerService.DEFAULT_ASSIGNEES`
4. Create `routers/<vertical>_router.py`
5. Register in `startup.py`

No core engine changes required.

See [VERTICALS.md](VERTICALS.md) for registry details.
