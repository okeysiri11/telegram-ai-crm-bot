"""Port registry and terminal management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.config import DEFAULT_CONFIG
from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PortRegistry:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register_port(self, *, name: str, unlocode: str = "", country: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("port name required")
        pid = _id("pe_port")
        return self.store.ports.save(
            pid,
            {
                "port_id": pid,
                "name": name,
                "unlocode": unlocode,
                "country": country,
                "created_at": _now(),
            },
        )

    def register_terminal(self, *, port_id: str, name: str, terminal_type: str = "container") -> dict[str, Any]:
        if self.store.ports.get(port_id) is None:
            raise NotFoundError("port", port_id)
        if terminal_type not in DEFAULT_CONFIG.terminal_types:
            raise ValidationError(f"terminal_type must be one of {DEFAULT_CONFIG.terminal_types}")
        tid = _id("pe_term")
        return self.store.terminals.save(
            tid,
            {
                "terminal_id": tid,
                "port_id": port_id,
                "name": name,
                "terminal_type": terminal_type,
                "created_at": _now(),
            },
        )

    def register_dock(self, *, terminal_id: str, name: str) -> dict[str, Any]:
        if self.store.terminals.get(terminal_id) is None:
            raise NotFoundError("terminal", terminal_id)
        did = _id("pe_dock")
        return self.store.docks.save(
            did, {"dock_id": did, "terminal_id": terminal_id, "name": name, "created_at": _now()}
        )

    def register_berth(self, *, dock_id: str, name: str, length_m: float = 300.0) -> dict[str, Any]:
        if self.store.docks.get(dock_id) is None:
            raise NotFoundError("dock", dock_id)
        bid = _id("pe_berth")
        return self.store.berths.save(
            bid,
            {
                "berth_id": bid,
                "dock_id": dock_id,
                "name": name,
                "length_m": float(length_m),
                "status": "available",
                "created_at": _now(),
            },
        )

    def register_warehouse(self, *, port_id: str, name: str, capacity_teu: float = 1000.0) -> dict[str, Any]:
        if self.store.ports.get(port_id) is None:
            raise NotFoundError("port", port_id)
        wid = _id("pe_wh")
        return self.store.warehouses.save(
            wid,
            {
                "warehouse_id": wid,
                "port_id": port_id,
                "name": name,
                "capacity_teu": float(capacity_teu),
                "created_at": _now(),
            },
        )

    def register_yard(self, *, port_id: str, name: str, capacity_teu: float = 5000.0) -> dict[str, Any]:
        if self.store.ports.get(port_id) is None:
            raise NotFoundError("port", port_id)
        yid = _id("pe_yard")
        return self.store.yards.save(
            yid,
            {
                "yard_id": yid,
                "port_id": port_id,
                "name": name,
                "capacity_teu": float(capacity_teu),
                "created_at": _now(),
            },
        )

    def register_equipment(self, *, terminal_id: str, name: str, equipment_type: str = "crane") -> dict[str, Any]:
        if self.store.terminals.get(terminal_id) is None:
            raise NotFoundError("terminal", terminal_id)
        eid = _id("pe_eq")
        return self.store.equipment.save(
            eid,
            {
                "equipment_id": eid,
                "terminal_id": terminal_id,
                "name": name,
                "equipment_type": equipment_type,
                "status": "operational",
                "created_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "ports": self.store.ports.count(),
            "terminals": self.store.terminals.count(),
            "docks": self.store.docks.count(),
            "berths": self.store.berths.count(),
            "warehouses": self.store.warehouses.count(),
            "yards": self.store.yards.count(),
            "equipment": self.store.equipment.count(),
        }


class TerminalManagement:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.types = list(DEFAULT_CONFIG.terminal_types)

    def set_capacity(self, *, terminal_id: str, capacity_teu: float, utilized_teu: float = 0.0) -> dict[str, Any]:
        if self.store.terminals.get(terminal_id) is None:
            raise NotFoundError("terminal", terminal_id)
        cid = _id("pe_cap")
        util = float(utilized_teu) / float(capacity_teu) if capacity_teu else 0.0
        return self.store.terminal_capacity.save(
            cid,
            {
                "capacity_id": cid,
                "terminal_id": terminal_id,
                "capacity_teu": float(capacity_teu),
                "utilized_teu": float(utilized_teu),
                "utilization_pct": round(util * 100, 2),
                "at": _now(),
            },
        )

    def utilization(self, terminal_id: str) -> dict[str, Any]:
        records = [c for c in self.store.terminal_capacity.list_all() if c.get("terminal_id") == terminal_id]
        if not records:
            raise NotFoundError("terminal_capacity", terminal_id)
        latest = records[-1]
        return latest

    def status(self) -> dict[str, Any]:
        return {
            "terminals": self.store.terminals.count(),
            "capacity_records": self.store.terminal_capacity.count(),
            "types": self.types,
        }
