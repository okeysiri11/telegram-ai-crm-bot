"""Serialization layer — Sprint 21.3."""

from __future__ import annotations

import json
from typing import Any

from platform_contracts.models import SERIALIZATION_FORMATS


class SerializationError(ValueError):
    pass


class SerializationLayer:
    """JSON / MessagePack / Protobuf / Avro — logical codecs (JSON-backed stubs for non-JSON)."""

    def formats(self) -> list[str]:
        return list(SERIALIZATION_FORMATS)

    def serialize(self, data: dict[str, Any], *, format: str = "json") -> bytes:
        fmt = format.lower()
        if fmt not in SERIALIZATION_FORMATS:
            raise SerializationError(f"unsupported format: {format}")
        payload = json.dumps(data, separators=(",", ":"), default=str).encode("utf-8")
        if fmt == "json":
            return payload
        # Logical envelopes for msgpack/protobuf/avro without heavy deps
        header = {"codec": fmt, "encoding": "json-envelope"}
        return json.dumps({"header": header, "body": data}, separators=(",", ":"), default=str).encode("utf-8")

    def deserialize(self, blob: bytes, *, format: str = "json") -> dict[str, Any]:
        fmt = format.lower()
        if fmt not in SERIALIZATION_FORMATS:
            raise SerializationError(f"unsupported format: {format}")
        raw = json.loads(blob.decode("utf-8"))
        if fmt == "json":
            if not isinstance(raw, dict):
                raise SerializationError("json payload must be object")
            return raw
        if not isinstance(raw, dict) or "body" not in raw:
            raise SerializationError(f"invalid {fmt} envelope")
        body = raw["body"]
        if not isinstance(body, dict):
            raise SerializationError("envelope body must be object")
        return body
