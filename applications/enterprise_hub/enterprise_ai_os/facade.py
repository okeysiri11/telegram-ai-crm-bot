"""Enterprise AI OS (Multi-Agent) Suite — Sprint 27.1."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from platform_ai_os.facade import MultiAgentOSLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store

ROOT = Path(__file__).resolve().parents[3]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EnterpriseAIOSSuite:
    """Sprint 27.1 Multi-Agent Executive Layer (distinct from AutonomousAIOSSuite)."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = MultiAgentOSLibrary()

    def bootstrap(self) -> dict[str, Any]:
        self.library = MultiAgentOSLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        web = ROOT / "src" / "web" / "ai-os"
        result["ai_os_path_exists"] = web.exists()
        result["dashboard_page_exists"] = (web / "pages" / "AIOSPage.tsx").exists()
        result["platform_package_exists"] = (ROOT / "platform_ai_os" / "facade.py").exists()
        result["hub_bridge_exists"] = (
            ROOT / "applications" / "enterprise_hub" / "ai_os" / "enterprise_multi_agent.py"
        ).exists()
        bid = _id("maos_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "hub_version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.maos_bootstraps.save(bid, record)
        for key, attr, prefix in (
            ("inventory", "maos_inventory", "maos_inv"),
            ("dashboard", "maos_dashboards", "maos_dash"),
            ("links", "maos_integrations", "maos_int"),
            ("registry", "maos_registry", "maos_reg"),
            ("bus", "maos_bus", "maos_bus"),
            ("memory", "maos_memory", "maos_mem"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        return record

    def inventory(self) -> dict[str, Any]:
        inv = self.library.inventory()
        rid = _id("maos_inv")
        record = {"inventory_id": rid, **inv, "created_at": _now()}
        self.store.maos_inventory.save(rid, record)
        return record

    def dashboard(self) -> dict[str, Any]:
        dash = self.library.dashboard()
        rid = _id("maos_dash")
        record = {"dashboard_id": rid, **dash, "created_at": _now()}
        self.store.maos_dashboards.save(rid, record)
        return record

    def executive(self, goal: str, **kwargs: Any) -> dict[str, Any]:
        result = self.library.executive_submit(goal, **kwargs)
        rid = _id("maos_exec")
        self.store.maos_executions.save(rid, {"execution_id": rid, **result, "created_at": _now()})
        return result

    def agents(self) -> dict[str, Any]:
        return self.library.agent_registry()

    def bus_publish(self, msg_type: str, **kwargs: Any) -> dict[str, Any]:
        return self.library.bus_publish(msg_type, **kwargs)

    def bus(self) -> dict[str, Any]:
        return self.library.bus_status()

    def orchestrate(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.orchestrate(**kwargs)
        rid = _id("maos_orch")
        self.store.maos_orchestrations.save(rid, {"orch_id": rid, **result, "created_at": _now()})
        return result

    def memory_write(self, **kwargs: Any) -> dict[str, Any]:
        return self.library.memory_write(**kwargs)

    def memory(self, layer: str | None = None) -> dict[str, Any]:
        return self.library.memory_read(layer)

    def collaborate(self, **kwargs: Any) -> dict[str, Any]:
        return self.library.collaborate(**kwargs)

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.maos_bootstraps.list_all()),
            "path": "src/web/ai-os",
            "api_prefix": "/api/ai-os/v1",
        }


enterprise_ai_os = EnterpriseAIOSSuite()
