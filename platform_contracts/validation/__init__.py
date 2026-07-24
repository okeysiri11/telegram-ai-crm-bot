"""DTO / event validation — Sprint 21.3."""

from __future__ import annotations

from typing import Any, Callable

from platform_contracts.dto.base.base_dto import BaseDTO
from platform_contracts.events.base import BaseEvent
from platform_contracts.models import BASE_DTO_FIELDS, EVENT_REQUIRED_FIELDS


class ValidationError(ValueError):
    pass


Validator = Callable[[dict[str, Any]], None]


class ValidationFramework:
    def __init__(self) -> None:
        self._custom: list[Validator] = []

    def add_validator(self, fn: Validator) -> None:
        self._custom.append(fn)

    def validate_dto(self, dto: BaseDTO | dict[str, Any]) -> dict[str, Any]:
        data = dto.to_dict() if isinstance(dto, BaseDTO) else dict(dto)
        missing = [f for f in ("id", "version", "created_at", "updated_at") if not data.get(f) and data.get(f) != 0]
        if missing:
            raise ValidationError(f"DTO missing required fields: {', '.join(missing)}")
        if not isinstance(data.get("version"), int) or data["version"] < 1:
            raise ValidationError("version must be int >= 1")
        if data.get("metadata") is not None and not isinstance(data["metadata"], dict):
            raise ValidationError("metadata must be a dict")
        for fn in self._custom:
            fn(data)
        return {"valid": True, "fields": list(BASE_DTO_FIELDS), "id": data.get("id")}

    def validate_event(self, event: BaseEvent | dict[str, Any]) -> dict[str, Any]:
        data = event.to_dict() if isinstance(event, BaseEvent) else dict(event)
        missing = [f for f in EVENT_REQUIRED_FIELDS if f not in data or data[f] in (None, "")]
        # payload may be empty dict
        missing = [f for f in missing if f != "payload" or "payload" not in data]
        if "payload" not in data:
            missing.append("payload")
        if missing:
            raise ValidationError(f"event missing fields: {', '.join(missing)}")
        if not isinstance(data.get("schema_version"), int):
            raise ValidationError("schema_version must be int")
        for fn in self._custom:
            fn(data)
        return {"valid": True, "event_id": data.get("event_id")}
