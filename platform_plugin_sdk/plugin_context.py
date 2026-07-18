# PluginContext — public SDK surface (no Platform Core internals exposed).

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TYPE_CHECKING

from platform_plugin_sdk.models import PluginConfigSchema, PluginMetadata
from platform_plugin_sdk.plugin_api import (
    ConfigurationApi,
    EventsApi,
    IamApi,
    IntegrationsApi,
    JobsApi,
    ManagementApi,
    ObservabilityApi,
    SdkApi,
    WorkflowApi,
)
from platform_plugin_sdk.plugin_configuration import PluginConfiguration
from platform_plugin_sdk.plugin_hooks import PluginHookRegistry
from platform_plugin_sdk.plugin_integrations import PluginIntegrations
from platform_plugin_sdk.plugin_logging import PluginLogger
from platform_plugin_sdk.plugin_metrics import PluginMetrics
from platform_plugin_sdk.plugin_permissions import PluginPermissions
from platform_plugin_sdk.plugin_realtime import PluginRealtime
from platform_plugin_sdk.plugin_scheduler import PluginScheduler
from platform_plugin_sdk.plugin_storage import PluginStorage

if TYPE_CHECKING:
    from aiohttp import web


@dataclass
class PluginContext:
    """
    Official extension API context.

    Plugin developers interact ONLY with this object and PlatformPlugin.
    Platform Core internals are never exposed.
    """

    plugin_id: str
    version: str
    metadata: PluginMetadata
    config: dict[str, Any] = field(default_factory=dict)
    plugin_path: str | None = None
    _app: web.Application | None = field(default=None, repr=False)

    # Lazy facades
    _events: EventsApi | None = field(default=None, repr=False)
    _jobs: JobsApi | None = field(default=None, repr=False)
    _workflow: WorkflowApi | None = field(default=None, repr=False)
    _configuration: ConfigurationApi | None = field(default=None, repr=False)
    _iam: IamApi | None = field(default=None, repr=False)
    _integrations: PluginIntegrations | None = field(default=None, repr=False)
    _observability: ObservabilityApi | None = field(default=None, repr=False)
    _sdk: SdkApi | None = field(default=None, repr=False)
    _realtime: PluginRealtime | None = field(default=None, repr=False)
    _scheduler: PluginScheduler | None = field(default=None, repr=False)
    _storage: PluginStorage | None = field(default=None, repr=False)
    _plugin_config: PluginConfiguration | None = field(default=None, repr=False)
    _logger: PluginLogger | None = field(default=None, repr=False)
    _metrics: PluginMetrics | None = field(default=None, repr=False)
    _permissions: PluginPermissions | None = field(default=None, repr=False)
    _hooks: PluginHookRegistry | None = field(default=None, repr=False)

    def bind_app(self, app: web.Application) -> None:
        self._app = app

    @property
    def app(self) -> web.Application | None:
        return self._app

    # ---- Public services ----

    @property
    def events(self) -> EventsApi:
        if self._events is None:
            self._events = EventsApi()
        return self._events

    @property
    def event_bus(self) -> EventsApi:
        return self.events

    @property
    def jobs(self) -> PluginScheduler:
        if self._scheduler is None:
            self._scheduler = PluginScheduler(self.plugin_id, self._jobs_api())
        return self._scheduler

    def _jobs_api(self) -> JobsApi:
        if self._jobs is None:
            self._jobs = JobsApi()
        return self._jobs

    @property
    def workflow(self) -> WorkflowApi:
        if self._workflow is None:
            self._workflow = WorkflowApi()
        return self._workflow

    @property
    def configuration(self) -> PluginConfiguration:
        if self._plugin_config is None:
            schema = PluginConfigSchema(defaults=dict(self.config))
            config_dir = Path(self.plugin_path) / "config" if self.plugin_path else None
            self._plugin_config = PluginConfiguration(self.plugin_id, schema, config_dir)
        return self._plugin_config

    @property
    def platform_config(self) -> ConfigurationApi:
        if self._configuration is None:
            self._configuration = ConfigurationApi()
        return self._configuration

    @property
    def iam(self) -> IamApi:
        if self._iam is None:
            self._iam = IamApi()
        return self._iam

    @property
    def integrations(self) -> PluginIntegrations:
        if self._integrations is None:
            self._integrations = PluginIntegrations(self.plugin_id, IntegrationsApi())
        return self._integrations

    @property
    def observability(self) -> ObservabilityApi:
        if self._observability is None:
            self._observability = ObservabilityApi()
        return self._observability

    @property
    def sdk(self) -> SdkApi:
        if self._sdk is None:
            self._sdk = SdkApi(self.plugin_id)
        return self._sdk

    @property
    def management(self) -> type[ManagementApi]:
        return ManagementApi

    @property
    def realtime(self) -> PluginRealtime:
        if self._realtime is None:
            self._realtime = PluginRealtime(self.plugin_id)
        return self._realtime

    @property
    def storage(self) -> PluginStorage:
        if self._storage is None:
            self._storage = PluginStorage(self.plugin_id)
        return self._storage

    @property
    def logger(self) -> PluginLogger:
        if self._logger is None:
            self._logger = PluginLogger(self.plugin_id)
        return self._logger

    @property
    def metrics(self) -> PluginMetrics:
        if self._metrics is None:
            self._metrics = PluginMetrics(self.plugin_id, self.observability)
        return self._metrics

    @property
    def permissions(self) -> PluginPermissions:
        if self._permissions is None:
            self._permissions = PluginPermissions(self.plugin_id, self.metadata.permissions)
        return self._permissions

    @property
    def hooks(self) -> PluginHookRegistry:
        if self._hooks is None:
            self._hooks = PluginHookRegistry(self.plugin_id)
        return self._hooks

    def get_config(self, key: str, default: Any = None) -> Any:
        return self.configuration.get(key, default)

    def log(self, message: str) -> None:
        self.logger.info(message)

    async def publish_event(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        from platform_plugin_sdk.plugin_events import SdkPluginBusEvent

        await self.events.publish(
            SdkPluginBusEvent(
                plugin_id=self.plugin_id,
                plugin_event_type=event_type,
                payload=payload or {},
            )
        )
