"""Connected Cars core — identity, connectivity, IoT gateway, edge, communications."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

DEVICE_KINDS = ["obd", "tracker", "edge", "gateway", "sensor"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ConnectedCarsCore:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def register_vehicle(self, *, vin: str, label: str = "", fleet_id: str = "") -> dict[str, Any]:
        vin = (vin or "").strip().upper()
        if len(vin) < 11:
            raise ValidationError("vin required")
        vid = _id("cc_veh")
        vehicle = {
            "connected_vehicle_id": vid,
            "vin": vin,
            "label": label or vin[-6:],
            "fleet_id": fleet_id,
            "connectivity": "offline",
            "identity_status": "registered",
            "created_at": _now(),
        }
        return self.store.cc_vehicles.save(vid, vehicle)

    def connect_vehicle(self, connected_vehicle_id: str, *, protocol: str = "mqtt") -> dict[str, Any]:
        vehicle = self.store.cc_vehicles.get(connected_vehicle_id)
        if vehicle is None:
            raise NotFoundError("connected_vehicle", connected_vehicle_id)
        vehicle["connectivity"] = "online"
        vehicle["protocol"] = protocol
        vehicle["connected_at"] = _now()
        self.store.cc_vehicles.save(connected_vehicle_id, vehicle)
        tid = _id("cc_hub")
        hub = {
            "telematics_session_id": tid,
            "connected_vehicle_id": connected_vehicle_id,
            "vin": vehicle["vin"],
            "protocol": protocol,
            "status": "active",
            "at": _now(),
        }
        return self.store.cc_telematics_hub.save(tid, hub)

    def register_iot_device(
        self,
        *,
        connected_vehicle_id: str,
        kind: str = "obd",
        serial: str = "",
    ) -> dict[str, Any]:
        if self.store.cc_vehicles.get(connected_vehicle_id) is None:
            raise NotFoundError("connected_vehicle", connected_vehicle_id)
        if kind not in DEVICE_KINDS:
            raise ValidationError(f"kind must be one of {DEVICE_KINDS}")
        did = _id("cc_iot")
        device = {
            "device_id": did,
            "connected_vehicle_id": connected_vehicle_id,
            "kind": kind,
            "serial": serial or did,
            "status": "provisioned",
            "created_at": _now(),
        }
        self.store.cc_iot_devices.save(did, device)
        if kind == "gateway":
            self.store.cc_iot_gateway.save(
                did,
                {"gateway_id": did, "connected_vehicle_id": connected_vehicle_id, "status": "up", "at": _now()},
            )
        if kind == "edge":
            self.store.cc_edge_devices.save(
                did,
                {"edge_id": did, "connected_vehicle_id": connected_vehicle_id, "status": "ready", "at": _now()},
            )
        return device

    def send_message(self, *, connected_vehicle_id: str, channel: str = "telematics", payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.store.cc_vehicles.get(connected_vehicle_id) is None:
            raise NotFoundError("connected_vehicle", connected_vehicle_id)
        mid = _id("cc_msg")
        msg = {
            "message_id": mid,
            "connected_vehicle_id": connected_vehicle_id,
            "channel": channel,
            "payload": payload or {},
            "status": "sent",
            "at": _now(),
        }
        return self.store.cc_communications.save(mid, msg)

    def status(self) -> dict[str, Any]:
        return {
            "vehicles": self.store.cc_vehicles.count(),
            "telematics_sessions": self.store.cc_telematics_hub.count(),
            "iot_devices": self.store.cc_iot_devices.count(),
            "messages": self.store.cc_communications.count(),
        }
