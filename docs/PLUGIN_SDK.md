# Plugin SDK Developer Guide

The **Platform Plugin SDK** (`platform_plugin_sdk`) is the official extension API for building business domain plugins. Plugin developers must **only** import from this package — never from `platform_plugins`, `platform_jobs`, or other Platform Core internals.

## Quick Start

### 1. Bootstrap a plugin

```bash
python -m platform_plugin_sdk.cli finance --name "Finance" --author "Your Team"
```

### 2. Implement your plugin

```python
from platform_plugin_sdk import PlatformPlugin, PluginContext
from platform_plugin_sdk.models import PluginHealthResult

class FinancePlugin(PlatformPlugin):
    plugin_id = "finance"
    name = "Finance"
    version = "1.0.0"

    async def on_enable(self, ctx: PluginContext) -> None:
        ctx.logger.info("Finance enabled")

    async def health(self) -> PluginHealthResult:
        return PluginHealthResult(status="healthy")

def create_plugin() -> PlatformPlugin:
    return FinancePlugin()
```

### 3. Install and enable

```bash
POST /management/plugins/finance/install
POST /management/plugins/finance/enable
```

## PluginContext Services

| Service | Access | Purpose |
|---------|--------|---------|
| Configuration | `ctx.configuration` | Plugin-private settings |
| Platform config | `ctx.platform_config` | Read platform feature flags |
| Jobs | `ctx.jobs` | Schedule namespaced background jobs |
| Realtime | `ctx.realtime` | Publish dashboard/widget updates |
| SDK | `ctx.sdk` | Vertical SDK context |
| Workflow | `ctx.workflow` | List/run workflows |
| EventBus | `ctx.events` | Publish/subscribe events |
| IAM | `ctx.iam` | Authorization checks |
| Integrations | `ctx.integrations` | Telegram, email, HTTP |
| Observability | `ctx.observability` | Metrics |
| Management | `ctx.management` | API path metadata |
| Storage | `ctx.storage` | Isolated namespaced storage |
| Logger | `ctx.logger` | Namespaced logging |
| Metrics | `ctx.metrics` | Plugin-tagged metrics |
| Permissions | `ctx.permissions` | Declared permissions |
| Hooks | `ctx.hooks` | Register custom hooks |

## Lifecycle

1. `initialize()` — load storage, validate config
2. `start()` — wire event hooks, run `on_enable`
3. `stop()` — run `on_disable`, unwire hooks
4. `reload()` — hot reload
5. `health()` — return `PluginHealthResult`
6. `shutdown()` — cleanup on uninstall

## Hooks

Override hook methods on `PlatformPlugin`:

- `on_install`, `on_enable`, `on_disable`, `on_reload`
- `on_request_created`, `on_request_completed`
- `on_workflow_started`, `on_workflow_completed`
- `on_configuration_changed`, `on_job_completed`, `on_event`

Platform events are automatically bridged when the plugin is started.

## Storage

```python
ctx.storage.set("counter", 1)
value = ctx.storage.get("counter", 0)
ctx.storage.register_migration(1, lambda data: {**data, "migrated": True})
ctx.storage.migrate(1)
```

## Scheduling Jobs

```python
async def my_handler(payload):
    return {"ok": True}

ctx.jobs.register("sync", my_handler)
await ctx.jobs.enqueue("sync", {"force": True})
await ctx.jobs.schedule_cron("sync", {}, "0 * * * *")
```

## Realtime Updates

```python
await ctx.realtime.publish_widget_update("top_kpis", {"value": 42})
await ctx.realtime.publish_plugin_status("healthy")
```

## Rules

1. **Never** import Platform Core modules in plugin code
2. Use **only** `platform_plugin_sdk` public exports
3. Declare permissions in `manifest.yaml`
4. Use namespaced job handlers via `ctx.jobs`
5. Store plugin data in `ctx.storage`, not global state

## Example Plugin

See `plugins/example/` for a complete reference implementation.
