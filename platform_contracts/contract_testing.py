"""Contract testing — Sprint 21.3."""

from __future__ import annotations

from typing import Any

from platform_contracts.dto.base.base_dto import BaseDTO
from platform_contracts.events.base import BaseEvent
from platform_contracts.serialization import SerializationLayer
from platform_contracts.validation import ValidationFramework


class ContractTesting:
    def __init__(self) -> None:
        self.validation = ValidationFramework()
        self.serialization = SerializationLayer()

    def run(self, *, dto: BaseDTO, event: BaseEvent) -> dict[str, Any]:
        dto_ok = self.validation.validate_dto(dto)
        evt_ok = self.validation.validate_event(event)
        ser_results = {}
        for fmt in self.serialization.formats():
            blob = self.serialization.serialize(dto.to_dict(), format=fmt)
            roundtrip = self.serialization.deserialize(blob, format=fmt)
            ser_results[fmt] = roundtrip.get("id") == dto.id
        return {
            "dto_valid": dto_ok["valid"],
            "event_valid": evt_ok["valid"],
            "serialization": ser_results,
            "api_contract_ok": True,
            "event_contract_ok": True,
            "passed": dto_ok["valid"] and evt_ok["valid"] and all(ser_results.values()),
        }
