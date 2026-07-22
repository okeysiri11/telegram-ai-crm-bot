from __future__ import annotations

import re
from typing import Any

from applications.drone_platform.firmware.repository import FirmwareRepository, firmware_repository
from applications.drone_platform.shared.exceptions import ValidationError


PARAM_LINE_RE = re.compile(r"^([A-Za-z0-9_]+)\s*,?\s*(-?\d+(?:\.\d+)?)\s*$")


class FirmwareAnalyzer:
    """Analyze firmware / param / mission engineering artifacts."""

    def __init__(self, repository: FirmwareRepository | None = None) -> None:
        self.repository = repository or firmware_repository

    def analyze_artifact(self, artifact_id: str) -> dict[str, Any]:
        art = self.repository.get(artifact_id)
        ext = art.get("artifact_type", "")
        content = art.get("content") or ""
        result: dict[str, Any] = {
            "artifact_id": artifact_id,
            "artifact_type": ext,
            "sha256": art.get("sha256"),
            "size_bytes": art.get("size_bytes"),
            "findings": [],
        }
        if ext in {".param", ".param.bak", ".backup"} or ext.endswith(".param"):
            params = self.parse_param_file(content)
            result["parameter_count"] = len(params)
            result["parameters_sample"] = dict(list(params.items())[:20])
            result["findings"].append("param_file_parsed")
        elif ext in {".bin", ".hex", ".apj"}:
            result["findings"].append("binary_metadata_only")
            result["notes"] = "Binary content treated as opaque engineering blob; no execution."
        elif ext in {".waypoints", ".mission"}:
            lines = [l for l in content.splitlines() if l.strip() and not l.startswith("#")]
            result["waypoint_lines"] = len(lines)
            result["findings"].append("mission_or_waypoint_file")
        elif ext == ".dump":
            result["findings"].append("configuration_dump")
            result["line_count"] = len(content.splitlines())
        else:
            result["findings"].append("generic_artifact")
        return result

    def parse_param_file(self, content: str) -> dict[str, float | int | str]:
        params: dict[str, float | int | str] = {}
        for raw in content.splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue
            if "," in line:
                parts = [p.strip() for p in line.split(",")]
            elif "\t" in line:
                parts = [p.strip() for p in line.split("\t")]
            elif " " in line:
                parts = line.split(None, 1)
            else:
                continue
            if len(parts) < 2:
                continue
            key, val = parts[0], parts[1]
            try:
                if "." in val:
                    params[key] = float(val)
                else:
                    params[key] = int(val)
            except ValueError:
                params[key] = val
        return params

    def analyze_param_text(self, content: str) -> dict[str, Any]:
        params = self.parse_param_file(content)
        return {"parameter_count": len(params), "parameters": params}


firmware_analyzer = FirmwareAnalyzer()
