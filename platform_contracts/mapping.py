"""Mapping engine — Sprint 21.3."""

from __future__ import annotations

from typing import Any, Callable

from platform_contracts.dto.base.base_dto import BaseDTO
from platform_contracts.events.base import BaseEvent


Mapper = Callable[[dict[str, Any]], dict[str, Any]]


class MappingEngine:
    def __init__(self) -> None:
        self._mappers: dict[str, Mapper] = {}

    def register(self, name: str, fn: Mapper) -> None:
        self._mappers[name] = fn

    def map(self, name: str, data: dict[str, Any]) -> dict[str, Any]:
        fn = self._mappers.get(name)
        if not fn:
            raise KeyError(f"mapper not found: {name}")
        return fn(data)

    def entity_to_dto(self, entity: dict[str, Any], *, dto_cls: type[BaseDTO] = BaseDTO) -> BaseDTO:
        payload = dict(entity)
        if "id" not in payload and "entity_id" in payload:
            payload["id"] = payload["entity_id"]
        return dto_cls.from_dict(payload)

    def dto_to_entity(self, dto: BaseDTO) -> dict[str, Any]:
        data = dto.to_dict()
        return {"entity_id": data["id"], **{k: v for k, v in data.items() if k != "id"}}

    def dto_to_event(self, dto: BaseDTO, *, event_type: str = "domain.entity.updated") -> BaseEvent:
        return BaseEvent(
            event_type=event_type,
            aggregate_id=dto.id,
            aggregate_type=getattr(dto, "entity_type", "entity"),
            source_service="contracts",
            actor="mapper",
            payload=dto.to_dict(),
            schema_version=int(dto.version),
            trace_id=dto.correlation_id,
        )

    def event_to_dto(self, event: BaseEvent, *, dto_cls: type[BaseDTO] = BaseDTO) -> BaseDTO:
        payload = dict(event.payload or {})
        payload.setdefault("id", event.aggregate_id or event.event_id)
        payload.setdefault("version", event.schema_version)
        payload.setdefault("correlation_id", event.trace_id)
        return dto_cls.from_dict(payload)

    def api_to_domain(self, body: dict[str, Any]) -> dict[str, Any]:
        return {"domain": body.get("domain", "common"), "data": body.get("data") or body}

    def domain_to_api(self, domain_obj: dict[str, Any]) -> dict[str, Any]:
        return {"success": True, "data": domain_obj}
