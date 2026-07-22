"""Flight log parsing and AI analysis (Sprint 11.3)."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.mavlink.parser import mavlink_parser
from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


SUPPORTED_LOG_TYPES = (
    ".bin",
    ".tlog",
    ".log",
    ".dataflash",
    "mavlink",
    "mission_planner",
    "qgroundcontrol",
    "ardupilot_dataflash",
    "px4_ulog",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FlightLogParser:
    def detect_type(self, *, filename: str = "", content: str = "", log_type: str = "") -> str:
        if log_type:
            return log_type
        name = filename.lower()
        for ext in (".bin", ".tlog", ".log", ".ulg", ".dataflash"):
            if name.endswith(ext):
                if ext == ".ulg":
                    return "px4_ulog"
                if ext == ".dataflash":
                    return "ardupilot_dataflash"
                return ext
        if "FMT," in content or "PARM," in content:
            return "ardupilot_dataflash"
        if content.strip().startswith("{") and "mavpackettype" in content:
            return "mavlink"
        if "QGC WPL" in content or "QGC" in content[:80]:
            return "qgroundcontrol"
        if "Mission Planner" in content or filename.lower().endswith(".tlog"):
            return "mission_planner"
        return "mavlink"

    def parse(self, *, content: str, filename: str = "", log_type: str = "") -> dict[str, Any]:
        detected = self.detect_type(filename=filename, content=content, log_type=log_type)
        if detected == "px4_ulog":
            return {
                "log_type": detected,
                "architecture_ready": True,
                "parsed": False,
                "note": "PX4 ULog architecture ready — full binary decode deferred",
                "messages": [],
                "parameters": {},
                "events": [],
            }
        messages: list[dict[str, Any]] = []
        parameters: dict[str, Any] = {}
        events: list[dict[str, Any]] = []
        if detected in {".tlog", "mavlink", "mission_planner"}:
            messages = mavlink_parser.parse_many(content)
        elif detected in {".log", "ardupilot_dataflash", ".dataflash", ".bin"}:
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("PARM,") or line.startswith("PARM "):
                    parts = re.split(r"[,\s]+", line)
                    if len(parts) >= 3:
                        parameters[parts[1]] = self._coerce(parts[2])
                elif line.startswith("MSG,") or "ERROR" in line.upper() or "FAILSAFE" in line.upper():
                    events.append({"raw": line, "kind": "status"})
                elif "," in line:
                    parts = line.split(",")
                    messages.append({"msg_name": parts[0], "fields": {"raw": parts[1:]}, "known": False})
        elif detected == "qgroundcontrol":
            for line in content.splitlines():
                if line.startswith("QGC") or not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 11:
                    messages.append(
                        {
                            "msg_name": "MISSION_ITEM",
                            "fields": {
                                "seq": int(parts[0]),
                                "command": int(parts[3]),
                                "x": float(parts[8]),
                                "y": float(parts[9]),
                                "z": float(parts[10]),
                            },
                            "known": True,
                        }
                    )
        else:
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    messages = [mavlink_parser.parse(m) if isinstance(m, (str, dict)) else m for m in data]
                elif isinstance(data, dict):
                    messages = data.get("messages", [])
                    parameters = data.get("parameters", {})
            except json.JSONDecodeError:
                messages = mavlink_parser.parse_many(content)
        return {
            "log_type": detected,
            "architecture_ready": True,
            "parsed": True,
            "message_count": len(messages),
            "messages": messages,
            "parameters": parameters,
            "events": events,
        }

    @staticmethod
    def _coerce(value: str) -> Any:
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return value


class FlightLogAnalyzer:
    def analyze(self, parsed: dict[str, Any]) -> dict[str, Any]:
        messages = parsed.get("messages") or []
        events = list(parsed.get("events") or [])
        findings: list[str] = []
        for msg in messages:
            name = str(msg.get("msg_name", "")).upper()
            fields = msg.get("fields") or {}
            if name == "STATUSTEXT":
                text = str(fields.get("text", ""))
                events.append({"kind": "statustext", "text": text})
                if any(k in text.upper() for k in ("EKF", "GPS", "FAILSAFE", "CRASH", "ERROR")):
                    findings.append(text)
            if name == "GPS_RAW_INT" and int(fields.get("fix_sat", 12) or 12) < 6:
                findings.append("Low GPS satellite count")
            if name == "SYS_STATUS" and int(fields.get("battery_remaining", 100) or 100) < 15:
                findings.append("Low battery remaining")
        return {
            "findings": findings,
            "event_count": len(events),
            "events": events[:100],
            "message_count": len(messages),
            "severity": "high" if any("CRASH" in f.upper() for f in findings) else "medium" if findings else "low",
        }


class FlightLogService:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store
        self.parser = FlightLogParser()
        self.analyzer = FlightLogAnalyzer()

    def supported_types(self) -> list[str]:
        return list(SUPPORTED_LOG_TYPES)

    def ingest(
        self,
        *,
        name: str,
        content: str,
        filename: str = "",
        log_type: str = "",
        uav_id: str = "",
        mission_id: str = "",
    ) -> dict[str, Any]:
        if not content and log_type != "px4_ulog":
            raise ValidationError("log content required")
        parsed = self.parser.parse(content=content or "", filename=filename or name, log_type=log_type)
        analysis = self.analyzer.analyze(parsed)
        lid = f"flog_{uuid.uuid4().hex[:12]}"
        record = {
            "log_id": lid,
            "name": name,
            "filename": filename or name,
            "uav_id": uav_id,
            "mission_id": mission_id,
            "log_type": parsed["log_type"],
            "parsed": parsed,
            "analysis": analysis,
            "created_at": _now(),
        }
        self.store.flight_logs.save(lid, record)
        return record

    def get(self, log_id: str) -> dict[str, Any]:
        item = self.store.flight_logs.get(log_id)
        if item is None:
            raise NotFoundError("flight_log", log_id)
        return item

    def list(self) -> list[dict[str, Any]]:
        return self.store.flight_logs.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "flight_log_intelligence": "1.0",
            "supported_types": self.supported_types(),
            "log_count": self.store.flight_logs.count(),
            "px4_ulog_architecture_ready": True,
        }


flight_log_service = FlightLogService()
