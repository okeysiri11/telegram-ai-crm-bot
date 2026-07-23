"""Container registry, operations, and yard management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store

ISO_SIZES = ["20GP", "40GP", "40HC", "45HC", "20RF", "40RF"]
CONTAINER_STATUSES = ["empty", "full", "reserved", "in_yard", "on_vessel", "gate_out", "maintenance"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ContainerRegistry:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register(
        self,
        *,
        container_number: str,
        iso_type: str = "40HC",
        owner: str = "",
        status: str = "empty",
    ) -> dict[str, Any]:
        if not container_number:
            raise ValidationError("container_number required")
        if iso_type not in ISO_SIZES:
            raise ValidationError(f"iso_type must be one of {ISO_SIZES}")
        if status not in CONTAINER_STATUSES:
            raise ValidationError(f"status must be one of {CONTAINER_STATUSES}")
        cid = _id("cm_ctr")
        return self.store.cm_containers.save(
            cid,
            {
                "container_id": cid,
                "container_number": container_number.upper(),
                "iso_type": iso_type,
                "owner": owner,
                "status": status,
                "created_at": _now(),
            },
        )

    def set_status(self, container_id: str, *, status: str) -> dict[str, Any]:
        if status not in CONTAINER_STATUSES:
            raise ValidationError(f"status must be one of {CONTAINER_STATUSES}")
        ctr = self.store.cm_containers.get(container_id)
        if ctr is None:
            raise NotFoundError("container", container_id)
        ctr["status"] = status
        ctr["updated_at"] = _now()
        self.store.cm_containers.save(container_id, ctr)
        hid = _id("cm_hist")
        self.store.cm_history.save(
            hid, {"history_id": hid, "container_id": container_id, "status": status, "at": _now()}
        )
        return ctr

    def inspect(self, container_id: str, *, result: str = "pass", notes: str = "") -> dict[str, Any]:
        if self.store.cm_containers.get(container_id) is None:
            raise NotFoundError("container", container_id)
        iid = _id("cm_insp")
        return self.store.cm_inspections.save(
            iid,
            {
                "inspection_id": iid,
                "container_id": container_id,
                "result": result,
                "notes": notes,
                "at": _now(),
            },
        )

    def maintain(self, container_id: str, *, work: str) -> dict[str, Any]:
        if self.store.cm_containers.get(container_id) is None:
            raise NotFoundError("container", container_id)
        mid = _id("cm_mnt")
        self.set_status(container_id, status="maintenance")
        return self.store.cm_maintenance.save(
            mid, {"maintenance_id": mid, "container_id": container_id, "work": work, "at": _now()}
        )

    def history(self, container_id: str) -> list[dict[str, Any]]:
        return [h for h in self.store.cm_history.list_all() if h.get("container_id") == container_id]

    def status(self) -> dict[str, Any]:
        return {
            "containers": self.store.cm_containers.count(),
            "inspections": self.store.cm_inspections.count(),
            "maintenance": self.store.cm_maintenance.count(),
        }


class ContainerOperations:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def _require(self, container_id: str) -> dict[str, Any]:
        ctr = self.store.cm_containers.get(container_id)
        if ctr is None:
            raise NotFoundError("container", container_id)
        return ctr

    def gate_in(self, container_id: str, *, gate: str = "G1") -> dict[str, Any]:
        self._require(container_id)
        oid = _id("cm_gin")
        self.store.cm_containers.get(container_id)  # noqa: ensure exists
        ctr = self._require(container_id)
        ctr["status"] = "in_yard"
        self.store.cm_containers.save(container_id, ctr)
        return self.store.cm_ops.save(
            oid,
            {
                "operation_id": oid,
                "container_id": container_id,
                "op_type": "gate_in",
                "gate": gate,
                "at": _now(),
            },
        )

    def gate_out(self, container_id: str, *, gate: str = "G1") -> dict[str, Any]:
        self._require(container_id)
        oid = _id("cm_gout")
        ctr = self._require(container_id)
        ctr["status"] = "gate_out"
        self.store.cm_containers.save(container_id, ctr)
        return self.store.cm_ops.save(
            oid,
            {
                "operation_id": oid,
                "container_id": container_id,
                "op_type": "gate_out",
                "gate": gate,
                "at": _now(),
            },
        )

    def load(self, container_id: str, *, vessel_id: str) -> dict[str, Any]:
        self._require(container_id)
        oid = _id("cm_load")
        ctr = self._require(container_id)
        ctr["status"] = "on_vessel"
        self.store.cm_containers.save(container_id, ctr)
        return self.store.cm_ops.save(
            oid,
            {
                "operation_id": oid,
                "container_id": container_id,
                "op_type": "loading",
                "vessel_id": vessel_id,
                "at": _now(),
            },
        )

    def unload(self, container_id: str, *, vessel_id: str) -> dict[str, Any]:
        self._require(container_id)
        oid = _id("cm_uld")
        ctr = self._require(container_id)
        ctr["status"] = "in_yard"
        self.store.cm_containers.save(container_id, ctr)
        return self.store.cm_ops.save(
            oid,
            {
                "operation_id": oid,
                "container_id": container_id,
                "op_type": "unloading",
                "vessel_id": vessel_id,
                "at": _now(),
            },
        )

    def transship(self, container_id: str, *, from_vessel: str, to_vessel: str) -> dict[str, Any]:
        self._require(container_id)
        oid = _id("cm_tsx")
        return self.store.cm_ops.save(
            oid,
            {
                "operation_id": oid,
                "container_id": container_id,
                "op_type": "transshipment",
                "from_vessel": from_vessel,
                "to_vessel": to_vessel,
                "at": _now(),
            },
        )

    def transfer(self, container_id: str, *, from_slot: str, to_slot: str) -> dict[str, Any]:
        self._require(container_id)
        oid = _id("cm_xfr")
        return self.store.cm_ops.save(
            oid,
            {
                "operation_id": oid,
                "container_id": container_id,
                "op_type": "transfer",
                "from_slot": from_slot,
                "to_slot": to_slot,
                "at": _now(),
            },
        )

    def reserve(self, container_id: str, *, party: str) -> dict[str, Any]:
        self._require(container_id)
        oid = _id("cm_rsv")
        ctr = self._require(container_id)
        ctr["status"] = "reserved"
        self.store.cm_containers.save(container_id, ctr)
        return self.store.cm_ops.save(
            oid,
            {
                "operation_id": oid,
                "container_id": container_id,
                "op_type": "reservation",
                "party": party,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"operations": self.store.cm_ops.count()}


class YardManagement:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register_yard(self, *, name: str, capacity_teu: float = 10000.0) -> dict[str, Any]:
        if not name:
            raise ValidationError("yard name required")
        yid = _id("cm_yard")
        return self.store.cm_yards.save(
            yid,
            {
                "yard_id": yid,
                "name": name,
                "capacity_teu": float(capacity_teu),
                "occupied_teu": 0.0,
                "created_at": _now(),
            },
        )

    def create_block(self, *, yard_id: str, name: str, rows: int = 10, tiers: int = 5) -> dict[str, Any]:
        if self.store.cm_yards.get(yard_id) is None:
            raise NotFoundError("yard", yard_id)
        bid = _id("cm_blk")
        return self.store.cm_blocks.save(
            bid,
            {
                "block_id": bid,
                "yard_id": yard_id,
                "name": name,
                "rows": int(rows),
                "tiers": int(tiers),
                "created_at": _now(),
            },
        )

    def allocate_slot(
        self,
        *,
        block_id: str,
        row: int,
        bay: int,
        tier: int,
        container_id: str,
    ) -> dict[str, Any]:
        if self.store.cm_blocks.get(block_id) is None:
            raise NotFoundError("block", block_id)
        if self.store.cm_containers.get(container_id) is None:
            raise NotFoundError("container", container_id)
        sid = _id("cm_slot")
        slot = self.store.cm_slots.save(
            sid,
            {
                "slot_id": sid,
                "block_id": block_id,
                "row": int(row),
                "bay": int(bay),
                "tier": int(tier),
                "container_id": container_id,
                "position": f"{block_id}-{row:02d}-{bay:02d}-{tier}",
                "at": _now(),
            },
        )
        block = self.store.cm_blocks.get(block_id)
        yard = self.store.cm_yards.get(block["yard_id"])
        if yard:
            yard["occupied_teu"] = float(yard.get("occupied_teu") or 0) + 1.0
            self.store.cm_yards.save(yard["yard_id"], yard)
        return slot

    def optimize(self, yard_id: str) -> dict[str, Any]:
        yard = self.store.cm_yards.get(yard_id)
        if yard is None:
            raise NotFoundError("yard", yard_id)
        util = float(yard.get("occupied_teu") or 0) / max(float(yard.get("capacity_teu") or 1), 1)
        oid = _id("cm_yopt")
        return self.store.cm_yard_opts.save(
            oid,
            {
                "optimization_id": oid,
                "yard_id": yard_id,
                "utilization_pct": round(util * 100, 2),
                "strategy": "minimize_reshuffles",
                "at": _now(),
            },
        )

    def search(self, *, container_number: str = "", container_id: str = "") -> list[dict[str, Any]]:
        results = []
        for slot in self.store.cm_slots.list_all():
            ctr = self.store.cm_containers.get(slot.get("container_id", ""))
            if ctr is None:
                continue
            if container_id and ctr["container_id"] != container_id:
                continue
            if container_number and ctr.get("container_number") != container_number.upper():
                continue
            results.append({**slot, "container": ctr})
        return results

    def capacity(self, yard_id: str) -> dict[str, Any]:
        yard = self.store.cm_yards.get(yard_id)
        if yard is None:
            raise NotFoundError("yard", yard_id)
        return {
            "yard_id": yard_id,
            "capacity_teu": yard["capacity_teu"],
            "occupied_teu": yard.get("occupied_teu", 0),
            "available_teu": float(yard["capacity_teu"]) - float(yard.get("occupied_teu") or 0),
        }

    def status(self) -> dict[str, Any]:
        return {
            "yards": self.store.cm_yards.count(),
            "blocks": self.store.cm_blocks.count(),
            "slots": self.store.cm_slots.count(),
        }
