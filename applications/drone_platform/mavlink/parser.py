"""MAVLink parser — text/JSON/binary-ish frame decoding for intelligence layer."""

from __future__ import annotations

import json
import re
from typing import Any

from applications.drone_platform.mavlink.messages import MESSAGE_REGISTRY
from applications.drone_platform.shared.exceptions import ValidationError


class MAVLinkParser:
    """Parse MAVLink-like payloads used by the intelligence layer (not a wire stack)."""

    def parse(self, payload: str | dict[str, Any] | bytes) -> dict[str, Any]:
        if isinstance(payload, dict):
            return self._normalize(payload)
        if isinstance(payload, bytes):
            try:
                text = payload.decode("utf-8", errors="replace")
            except Exception as exc:
                raise ValidationError(f"Unable to decode bytes payload: {exc}") from exc
            return self.parse(text)
        text = payload.strip()
        if not text:
            raise ValidationError("Empty MAVLink payload")
        if text.startswith("{"):
            try:
                data = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"Invalid JSON MAVLink payload: {exc}") from exc
            return self._normalize(data)
        return self._parse_text_line(text)

    def parse_many(self, content: str) -> list[dict[str, Any]]:
        messages = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                messages.append(self.parse(line))
            except ValidationError:
                continue
        return messages

    def _parse_text_line(self, line: str) -> dict[str, Any]:
        # Formats: MSGNAME key=value ...  OR  MSGNAME:{json}
        if ":" in line and line.split(":", 1)[1].strip().startswith("{"):
            name, rest = line.split(":", 1)
            data = json.loads(rest)
            data["msg_name"] = name.strip().upper()
            return self._normalize(data)
        parts = line.split()
        name = parts[0].upper()
        fields: dict[str, Any] = {}
        for token in parts[1:]:
            if "=" in token:
                k, v = token.split("=", 1)
                fields[k] = self._coerce(v)
        return self._normalize({"msg_name": name, **fields})

    def _normalize(self, data: dict[str, Any]) -> dict[str, Any]:
        name = str(data.get("msg_name") or data.get("mavpackettype") or data.get("type") or "").upper()
        if not name:
            raise ValidationError("MAVLink message missing msg_name")
        meta = MESSAGE_REGISTRY.get(name, {})
        return {
            "msg_name": name,
            "msg_id": meta.get("id"),
            "category": meta.get("category", "unknown"),
            "fields": {k: v for k, v in data.items() if k not in {"msg_name", "mavpackettype", "type", "msg_id", "category", "fields"}},
            "known": name in MESSAGE_REGISTRY,
        }

    @staticmethod
    def _coerce(value: str) -> Any:
        if re.fullmatch(r"-?\d+", value):
            return int(value)
        if re.fullmatch(r"-?\d+\.\d+", value):
            return float(value)
        if value.lower() in {"true", "false"}:
            return value.lower() == "true"
        return value


mavlink_parser = MAVLinkParser()
