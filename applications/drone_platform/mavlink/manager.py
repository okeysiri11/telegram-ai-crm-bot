"""MAVLink connection profiles, router, heartbeat, discovery, protocols, streams."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.mavlink.commands import CommandRegistry, command_registry
from applications.drone_platform.mavlink.messages import MessageRegistry, message_registry
from applications.drone_platform.mavlink.parser import MAVLinkParser, mavlink_parser
from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConnectionProfiles:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def create(
        self,
        *,
        name: str,
        transport: str = "udp",
        endpoint: str = "udpin:0.0.0.0:14550",
        dialect: str = "ardupilotmega",
        baud: int = 57600,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        cid = f"mvc_{uuid.uuid4().hex[:12]}"
        profile = {
            "connection_id": cid,
            "name": name,
            "transport": transport,
            "endpoint": endpoint,
            "dialect": dialect,
            "baud": baud,
            "status": "configured",
            "metadata": dict(metadata or {}),
            "created_at": _now(),
        }
        self.store.mavlink_connections.save(cid, profile)
        return profile

    def get(self, connection_id: str) -> dict[str, Any]:
        item = self.store.mavlink_connections.get(connection_id)
        if item is None:
            raise NotFoundError("mavlink_connection", connection_id)
        return item

    def list(self) -> list[dict[str, Any]]:
        return self.store.mavlink_connections.list_all()

    def connect(self, connection_id: str) -> dict[str, Any]:
        profile = self.get(connection_id)
        profile["status"] = "connected"
        profile["connected_at"] = _now()
        self.store.mavlink_connections.save(connection_id, profile)
        return profile


class MAVLinkRouter:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def add_route(
        self,
        *,
        source_connection_id: str,
        target_connection_id: str,
        message_filter: list[str] | None = None,
        bidirectional: bool = True,
    ) -> dict[str, Any]:
        rid = f"mvr_{uuid.uuid4().hex[:12]}"
        route = {
            "route_id": rid,
            "source_connection_id": source_connection_id,
            "target_connection_id": target_connection_id,
            "message_filter": list(message_filter or []),
            "bidirectional": bidirectional,
            "status": "active",
            "forwarded": 0,
            "created_at": _now(),
        }
        self.store.mavlink_routes.save(rid, route)
        return route

    def forward(self, route_id: str, message: dict[str, Any]) -> dict[str, Any]:
        route = self.store.mavlink_routes.get(route_id)
        if route is None:
            raise NotFoundError("mavlink_route", route_id)
        filt = route.get("message_filter") or []
        name = str(message.get("msg_name", "")).upper()
        if filt and name not in [f.upper() for f in filt]:
            return {"forwarded": False, "reason": "filtered", "route_id": route_id}
        route["forwarded"] = int(route.get("forwarded", 0)) + 1
        route["last_forward_at"] = _now()
        self.store.mavlink_routes.save(route_id, route)
        return {"forwarded": True, "route_id": route_id, "message": message}

    def list(self) -> list[dict[str, Any]]:
        return self.store.mavlink_routes.list_all()


class HeartbeatMonitor:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def record(self, *, system_id: int, autopilot: str = "ardupilot", vehicle_type: str = "quadrotor", base_mode: int = 0) -> dict[str, Any]:
        hid = f"hb_{system_id}"
        beat = {
            "heartbeat_id": hid,
            "system_id": system_id,
            "autopilot": autopilot,
            "vehicle_type": vehicle_type,
            "base_mode": base_mode,
            "last_seen": _now(),
            "alive": True,
            "missed": 0,
        }
        self.store.mavlink_heartbeats.save(hid, beat)
        return beat

    def mark_missed(self, system_id: int) -> dict[str, Any]:
        hid = f"hb_{system_id}"
        beat = self.store.mavlink_heartbeats.get(hid)
        if beat is None:
            raise NotFoundError("mavlink_heartbeat", hid)
        beat["missed"] = int(beat.get("missed", 0)) + 1
        beat["alive"] = beat["missed"] < 3
        beat["updated_at"] = _now()
        self.store.mavlink_heartbeats.save(hid, beat)
        return beat

    def list(self) -> list[dict[str, Any]]:
        return self.store.mavlink_heartbeats.list_all()


class VehicleDiscovery:
    def __init__(self, store: DroneStore | None = None, heartbeats: HeartbeatMonitor | None = None) -> None:
        self.store = store or drone_store
        self.heartbeats = heartbeats or HeartbeatMonitor(self.store)

    def discover_from_heartbeat(self, heartbeat: dict[str, Any]) -> dict[str, Any]:
        system_id = int(heartbeat.get("system_id", 1))
        vid = f"veh_{system_id}"
        vehicle = {
            "vehicle_id": vid,
            "system_id": system_id,
            "autopilot": heartbeat.get("autopilot", "unknown"),
            "vehicle_type": heartbeat.get("vehicle_type", "unknown"),
            "discovered_at": _now(),
            "status": "online" if heartbeat.get("alive", True) else "stale",
        }
        self.store.mavlink_vehicles.save(vid, vehicle)
        return vehicle

    def list(self) -> list[dict[str, Any]]:
        return self.store.mavlink_vehicles.list_all()


class ParameterProtocol:
    def request_list(self, system_id: int = 1) -> dict[str, Any]:
        return {"protocol": "parameter", "action": "PARAM_REQUEST_LIST", "system_id": system_id, "status": "queued"}

    def set_param(self, *, param_id: str, value: float, system_id: int = 1) -> dict[str, Any]:
        if not param_id:
            raise ValidationError("param_id required")
        return {
            "protocol": "parameter",
            "action": "PARAM_SET",
            "system_id": system_id,
            "param_id": param_id,
            "param_value": value,
            "status": "queued",
        }


class FTPProtocol:
    def list_directory(self, path: str = "/") -> dict[str, Any]:
        return {"protocol": "ftp", "action": "list", "path": path, "entries": ["params/", "logs/", "missions/"], "status": "ok"}

    def download(self, path: str) -> dict[str, Any]:
        return {"protocol": "ftp", "action": "download", "path": path, "status": "queued", "bytes": 0}


class MissionProtocol:
    def request_list(self, system_id: int = 1) -> dict[str, Any]:
        return {"protocol": "mission", "action": "MISSION_REQUEST_LIST", "system_id": system_id, "status": "queued"}

    def upload(self, *, waypoints: list[dict[str, Any]], system_id: int = 1) -> dict[str, Any]:
        return {
            "protocol": "mission",
            "action": "MISSION_COUNT",
            "system_id": system_id,
            "count": len(waypoints),
            "waypoints": list(waypoints),
            "status": "queued",
        }


class TelemetryStreamManager:
    def __init__(self, store: DroneStore | None = None, parser: MAVLinkParser | None = None) -> None:
        self.store = store or drone_store
        self.parser = parser or mavlink_parser

    def open_stream(self, *, connection_id: str, name: str = "primary") -> dict[str, Any]:
        sid = f"stm_{uuid.uuid4().hex[:12]}"
        stream = {
            "stream_id": sid,
            "connection_id": connection_id,
            "name": name,
            "messages": [],
            "status": "open",
            "opened_at": _now(),
        }
        self.store.mavlink_streams.save(sid, stream)
        return stream

    def ingest(self, stream_id: str, payload: str | dict[str, Any]) -> dict[str, Any]:
        stream = self.store.mavlink_streams.get(stream_id)
        if stream is None:
            raise NotFoundError("mavlink_stream", stream_id)
        msg = self.parser.parse(payload)
        msg["received_at"] = _now()
        stream["messages"].append(msg)
        self.store.mavlink_streams.save(stream_id, stream)
        return msg

    def get(self, stream_id: str) -> dict[str, Any]:
        stream = self.store.mavlink_streams.get(stream_id)
        if stream is None:
            raise NotFoundError("mavlink_stream", stream_id)
        return stream

    def list(self) -> list[dict[str, Any]]:
        return self.store.mavlink_streams.list_all()


class MAVLinkManager:
    """Unified MAVLink intelligence facade (Sprint 11.3)."""

    def __init__(
        self,
        store: DroneStore | None = None,
        messages: MessageRegistry | None = None,
        commands: CommandRegistry | None = None,
        parser: MAVLinkParser | None = None,
    ) -> None:
        self.store = store or drone_store
        self.messages = messages or message_registry
        self.commands = commands or command_registry
        self.parser = parser or mavlink_parser
        self.connections = ConnectionProfiles(self.store)
        self.router = MAVLinkRouter(self.store)
        self.heartbeat = HeartbeatMonitor(self.store)
        self.discovery = VehicleDiscovery(self.store, self.heartbeat)
        self.parameters = ParameterProtocol()
        self.ftp = FTPProtocol()
        self.mission = MissionProtocol()
        self.streams = TelemetryStreamManager(self.store, self.parser)

    def status(self) -> dict[str, Any]:
        return {
            "mavlink_intelligence": "1.0",
            "message_count": len(self.messages.list_messages()),
            "command_count": len(self.commands.list_commands()),
            "connections": self.store.mavlink_connections.count(),
            "vehicles": self.store.mavlink_vehicles.count(),
            "streams": self.store.mavlink_streams.count(),
            "capabilities": [
                "manager",
                "router",
                "parser",
                "message_registry",
                "command_registry",
                "heartbeat_monitor",
                "parameter_protocol",
                "ftp_protocol",
                "mission_protocol",
                "telemetry_stream_manager",
                "vehicle_discovery",
                "connection_profiles",
            ],
        }


mavlink_manager = MAVLinkManager()
