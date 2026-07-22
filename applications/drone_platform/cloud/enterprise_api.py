"""Enterprise APIs — REST, GraphQL, WebSocket, MQTT, MAVLink, ROS2, MP, QGC (Sprint 11.8)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


ENTERPRISE_PROTOCOLS = (
    "rest",
    "graphql",
    "websocket",
    "mqtt",
    "mavlink",
    "ros2",
    "mission_planner",
    "qgroundcontrol",
)


class EnterpriseAPIs:
    def supported(self) -> list[str]:
        return list(ENTERPRISE_PROTOCOLS)

    def connect(self, *, protocol: str, endpoint: str = "") -> dict[str, Any]:
        key = protocol.lower().replace("-", "_")
        if key not in ENTERPRISE_PROTOCOLS:
            return {"connected": False, "protocol": protocol, "error": "unsupported"}
        return {
            "connected": True,
            "protocol": key,
            "endpoint": endpoint or f"{key}://drone-cloud/default",
            "at": _now(),
        }

    def rest_info(self) -> dict[str, Any]:
        return {"protocol": "rest", "base": "/api/drone/v1/cloud", "methods": ["GET", "POST"]}

    def graphql_schema(self) -> dict[str, Any]:
        return {
            "protocol": "graphql",
            "types": ["Aircraft", "Mission", "Fleet", "Incident", "Twin"],
            "query_root": "Query",
            "mutation_root": "Mutation",
        }

    def websocket_channels(self) -> dict[str, Any]:
        return {"protocol": "websocket", "channels": ["telemetry", "alerts", "tracks", "commands"]}

    def mqtt_topics(self) -> dict[str, Any]:
        return {"protocol": "mqtt", "topics": ["drone/+/telemetry", "drone/+/cmd", "fleet/+/status"]}

    def mavlink_bridge(self) -> dict[str, Any]:
        return {"protocol": "mavlink", "dialects": ["ardupilotmega", "common"], "router": "mavlink-router"}

    def ros2_bridge(self) -> dict[str, Any]:
        return {"protocol": "ros2", "topics": ["/drone/odom", "/drone/cmd_vel", "/mission/path"]}

    def gcs_bridges(self) -> dict[str, Any]:
        return {"mission_planner": True, "qgroundcontrol": True, "mavproxy": True}

    def status(self) -> dict[str, Any]:
        return {"enterprise_apis": "1.0", "protocols": self.supported(), "ready": True}


enterprise_apis = EnterpriseAPIs()
