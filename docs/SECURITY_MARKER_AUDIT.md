# Security Marker Audit — Sprint 30.0

Automated scan of backend `*.py` for security-relevant markers.
Occurrences are **documented**, not auto-deleted (many are legitimate).

## Counts

| Marker | Count |
|---|---:|
| `TODO` | 150 |
| `FIXME` | 2 |
| `HACK` | 2 |
| `temporary` | 13 |
| `deprecated` | 97 |
| `legacy` | 1176 |
| `unsafe` | 22 |
| `password` | 62 |
| `secret` | 446 |
| `jwt` | 265 |
| `token` | 837 |
| `admin` | 765 |
| `superuser` | 2 |

## Samples (up to 8 per marker)

### `TODO`

- `database_legacy.py:165` — `status TEXT DEFAULT 'todo',`
- `database_legacy.py:2635` — `# TODO: future implementation — cache roles per session`
- `database_legacy.py:2657` — `# TODO: future implementation — Telegram UI for role assignment`
- `database_legacy.py:2679` — `# TODO: future implementation — Telegram UI for role revocation`
- `database_legacy.py:4166` — `# TODO: future implementation — deprecated alias, use has_module_access`
- `database_legacy.py:4171` — `# TODO: future implementation — pagination, search, filters`
- `database_legacy.py:4185` — `# TODO: future implementation — rich user cards with roles`
- `database_legacy.py:4205` — `# TODO: future implementation — role editor with permissions preview`

### `FIXME`

- `scripts/security_marker_audit.py:4` — `Searches backend Python for TODO/FIXME/HACK/temporary/deprecated/legacy/unsafe/`
- `scripts/security_marker_audit.py:19` — `"FIXME",`

### `HACK`

- `scripts/security_marker_audit.py:4` — `Searches backend Python for TODO/FIXME/HACK/temporary/deprecated/legacy/unsafe/`
- `scripts/security_marker_audit.py:20` — `"HACK",`

### `temporary`

- `routers/auto_client_router.py:56` — `"""Temporary debug logging for all auto-client messages/callbacks."""`
- `routers/auto_client_router.py:769` — `# Temporary catch-all debug handlers (only Auto Client session — do not block other routers).`
- `platform_enterprise_navigation/facade.py:102` — `{"id": "ws_temp", "kind": "temporary", "name": "Temporary Workspace", "route": "/workspace?scope=temporary"},`
- `platform_enterprise_navigation/models.py:55` — `"temporary",`
- `tests/test_ai_memory.py:148` — `await memory_service.remember(RememberRequest(content="unrelated content about weather", memory_type=MemoryType.TEMPORAR`
- `scripts/security_marker_audit.py:4` — `Searches backend Python for TODO/FIXME/HACK/temporary/deprecated/legacy/unsafe/`
- `scripts/security_marker_audit.py:21` — `"temporary",`
- `applications/legal_enterprise/compliance/facade.py:73` — `control_id=control["control_id"], reason="Temporary vendor exception", approved_by="GC"`

### `deprecated`

- `database_legacy.py:4166` — `# TODO: future implementation — deprecated alias, use has_module_access`
- `platform_management/management_service.py:438` — `async def migration_deprecated() -> dict[str, Any]:`
- `platform_management/management_service.py:443` — `"deprecated_apis": deprecation_manager.list_deprecated(),`
- `platform_management/management_router.py:503` — `async def migration_deprecated_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:`
- `platform_management/management_router.py:504` — `return _ok(await management_service.migration_deprecated(), ctx)`
- `platform_management/management_router.py:584` — `_route(app, "GET", "migration/deprecated", migration_deprecated_handler, role=ManagementRole.READ_ONLY, summary="Depreca`
- `platform_api/__init__.py:10` — `deprecated,`
- `platform_api/__init__.py:25` — `"deprecated",`

### `legacy`

- `startup.py:35` — `from platform_legacy import legacy`
- `startup.py:37` — `legacy.telegram.register_bot_routers(dp)`
- `startup.py:62` — `from platform_legacy import legacy`
- `startup.py:64` — `legacy.bootstrap.configure_bidex_parser()`
- `startup.py:68` — `legacy.bootstrap.register_webhook_handlers()`
- `startup.py:79` — `scheduler = legacy.scheduler.get_default_worker()`
- `startup.py:122` — `seed = await legacy.permissions.ensure_permissions_seeded()`
- `startup.py:128` — `routing_seed = await legacy.bootstrap.ensure_vertical_routing()`

### `unsafe`

- `middleware/security_middleware.py:21` — `_UNSAFE_QUERY = re.compile(r"(--|/\*|\*/|;|\bunion\b|\bdrop\b|\bexec\b)", re.I)`
- `middleware/security_middleware.py:143` — `if _UNSAFE_QUERY.search(value):`
- `tests/test_drone_vision_autonomy.py:187` — `unsafe = drone_platform.ai.detect_unsafe_conditions(observations={"battery_pct": 10, "wind_mps": 15})`
- `tests/test_drone_vision_autonomy.py:188` — `assert unsafe["response"]["unsafe"] is True`
- `tests/test_migration_25_4.py:138` — `migration_id="mig_unsafe",`
- `tests/test_ai_os_12_4.py:86` — `ai_os.runtime.execute(name="bad", payload={"unsafe": True}, sandboxed=True)`
- `scripts/security_marker_audit.py:4` — `Searches backend Python for TODO/FIXME/HACK/temporary/deprecated/legacy/unsafe/`
- `scripts/security_marker_audit.py:24` — `"unsafe",`

### `password`

- `platform_security/facade.py:76` — `("database_password", "db-main", "db-pass"),`
- `platform_security/models.py:45` — `"database_password",`
- `platform_security/models.py:70` — `"password_spray",`
- `platform_enterprise_security_verification/models.py:63` — `"passwords",`
- `tests/test_security_layer.py:158` — `record = manager.store_secret("db_password", "super-secret")`
- `tests/test_external_pilot_32_1.py:122` — `json={"email": "owner32_1@example.com", "password": "Passw0rd!", "display_name": "Owner"},`
- `tests/test_external_pilot_32_1.py:157` — `json={"email": "member32_1@example.com", "password": "Passw0rd!", "display_name": "Member"},`
- `tests/test_ecosystem.py:44` — `password="secret123",`

### `secret`

- `startup.py:57` — `from platform_identity.jwt_service import validate_iam_jwt_secret`
- `startup.py:59` — `validate_iam_jwt_secret()`
- `config.py:73` — `S3_SECRET_KEY = _settings.storage.s3_secret_key`
- `config.py:76` — `JWT_SECRET = _settings.jwt.secret`
- `config.py:80` — `IAM_LOGIN_SECRET = _settings.jwt.login_secret`
- `platform_integrations/models.py:101` — `secret: str`
- `platform_integrations/models.py:106` — `def to_dict(self, *, include_secret: bool = False) -> dict[str, Any]:`
- `platform_integrations/models.py:116` — `if include_secret:`

### `jwt`

- `startup.py:57` — `from platform_identity.jwt_service import validate_iam_jwt_secret`
- `startup.py:59` — `validate_iam_jwt_secret()`
- `config.py:75` — `# ---- JWT / IAM ----`
- `config.py:76` — `JWT_SECRET = _settings.jwt.secret`
- `config.py:77` — `JWT_ALGORITHM = _settings.jwt.algorithm`
- `config.py:78` — `JWT_EXPIRE_MINUTES = _settings.jwt.expire_minutes`
- `config.py:79` — `IAM_SESSION_TTL_SECONDS = _settings.jwt.session_ttl_seconds`
- `config.py:80` — `IAM_LOGIN_SECRET = _settings.jwt.login_secret`

### `token`

- `bootstrap.py:10` — `from config import BOT_TOKEN`
- `bootstrap.py:17` — `bot = Bot(token=BOT_TOKEN)`
- `config.py:36` — `BOT_TOKEN = _settings.telegram.bot_token or None`
- `auto_vertical_handlers.py:12` — `from config import BOT_TOKEN, OWNER_ID`
- `auto_vertical_handlers.py:476` — `if not BOT_TOKEN:`
- `middleware/security_middleware.py:131` — `if "session" not in request.cookies and "csrftoken" not in request.cookies:`
- `middleware/security_middleware.py:133` — `header_token = request.headers.get("X-CSRF-Token", "")`
- `middleware/security_middleware.py:134` — `cookie_token = request.cookies.get("csrftoken", "")`

### `admin`

- `deal_engine_handlers.py:1` — `# Universal Deal Engine v1 — admin/owner views and lead conversion.`
- `deal_engine_handlers.py:14` — `from keyboards import admin_module_menu`
- `deal_engine_handlers.py:22` — `def _can_access_admin(user_id: int) -> bool:`
- `deal_engine_handlers.py:29` — `if not _can_access_admin(user_id):`
- `deal_engine_handlers.py:39` — `reply_markup=admin_module_menu(),`
- `deal_engine_handlers.py:42` — `await message.answer(text, reply_markup=admin_module_menu())`
- `deal_engine_handlers.py:43` — `log_audit(user_id, "open", "admin", "deal_dashboard")`
- `deal_engine_handlers.py:49` — `if not _can_access_admin(user_id):`

### `superuser`

- `scripts/security_marker_audit.py:5` — `password/secret/jwt/token/admin/superuser markers and writes a documented report.`
- `scripts/security_marker_audit.py:30` — `"superuser",`

## Disposition policy

- **Remove** only confirmed dead/unsafe code in a dedicated PR.
- **Document** intentional legacy/deprecated markers in `TECH_DEBT.md`.
- **Never** commit real passwords/secrets — if found, rotate immediately.

Hardening applied this sprint lives in `platform_security/`, `middleware/security_middleware.py`,
`repositories/tenant_scope.py`, and Platform Builder live-auth middleware.
