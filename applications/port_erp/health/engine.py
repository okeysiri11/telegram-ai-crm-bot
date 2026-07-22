# Health monitoring for Port ERP production release.

from __future__ import annotations

from typing import Any

from applications.port_erp.config import DEFAULT_CONFIG, PortERPConfig
from applications.port_erp.shared.store import PortStore, port_store


class HealthEngine:
    """Component health monitoring for Port ERP."""

    def __init__(
        self,
        store: PortStore | None = None,
        config: PortERPConfig | None = None,
    ) -> None:
        self._store = store or port_store
        self._config = config or DEFAULT_CONFIG

    def probe(self) -> dict[str, Any]:
        from applications.port_erp.integrations.ecosystem_bridge import ecosystem_bridge
        from applications.port_erp.integrations.platform_bridge import platform_bridge

        platform = platform_bridge.platform_health()
        ecosystem = ecosystem_bridge.ecosystem_health()
        platform_status = platform.get("status") or (
            "ok" if platform.get("platform_dependency") else "unknown"
        )
        ecosystem_status = ecosystem.get("status") or (
            "ok" if ecosystem.get("ecosystem_dependency") else "unknown"
        )
        components = {
            "store": "ok",
            "platform": platform_status,
            "ecosystem": ecosystem_status,
            "network_partners": "ok",
            "integrations": "ok",
        }
        healthy = all(v in ("ok", "available", "fallback") for v in components.values())
        return {
            "healthy": healthy,
            "application_version": self._config.application_version,
            "components": components,
            "platform": platform,
            "ecosystem": ecosystem,
        }


health_engine = HealthEngine()
