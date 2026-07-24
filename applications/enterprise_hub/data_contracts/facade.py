"""Data Contracts Suite facade — Sprint 21.3 / v6.0.0-rc3."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_contracts.facade import ContractsLibrary
from platform_contracts.dto.crm import ContactDTO
from platform_contracts.events.domain import EntityCreatedEvent

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DataContractsSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = ContractsLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations()

    def bootstrap(self) -> dict[str, Any]:
        self.library = ContractsLibrary()
        result = self.library.bootstrap()
        bid = _id("edc_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.edc_bootstraps.save(bid, record)
        # persist registry snapshots
        for dto in self.library.dto_registry.list_all():
            self.store.edc_dto_registry.save(dto["dto_id"], dto)
        for name in ("BaseDTO",):
            for ver in self.library.schema_registry.list_versions(name):
                self.store.edc_schemas.save(ver["schema_id"], ver)
        docs = self.library.docs.generate(
            dto_registry=self.library.dto_registry,
            schema_registry=self.library.schema_registry,
        )
        doc_id = _id("edc_doc")
        self.store.edc_docs.save(doc_id, {"doc_id": doc_id, **docs, "generated_at": _now()})
        record["doc_id"] = doc_id
        self.store.edc_bootstraps.save(bid, record)
        return record

    def register_dto(self, *, name: str, domain: str, fields: list[str] | None = None) -> dict[str, Any]:
        try:
            item = self.library.dto_registry.register(
                name=name,
                domain=domain,
                fields=fields or ["id", "version", "created_at", "updated_at", "metadata"],
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.edc_dto_registry.save(item["dto_id"], item)
        return item

    def publish_schema(self, *, name: str, schema: dict[str, Any], version: int | None = None) -> dict[str, Any]:
        try:
            item = self.library.schema_registry.publish(name=name, schema=schema, version=version)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.edc_schemas.save(item["schema_id"], item)
        return item

    def validate_dto(self, data: dict[str, Any]) -> dict[str, Any]:
        from platform_contracts.dto.base import BaseDTO
        from platform_contracts.validation import ValidationError as LibValidationError

        try:
            base = BaseDTO.from_dict({**BaseDTO().to_dict(), **data})
            result = self.library.validation.validate_dto(base)
        except LibValidationError as exc:
            raise ValidationError(str(exc)) from exc
        except Exception as exc:
            raise ValidationError(str(exc)) from exc
        vid = _id("edc_val")
        record = {"validation_id": vid, **result, "validated_at": _now()}
        self.store.edc_validations.save(vid, record)
        return record

    def serialize(self, data: dict[str, Any], *, format: str = "json") -> dict[str, Any]:
        try:
            blob = self.library.serialization.serialize(data, format=format)
        except Exception as exc:
            raise ValidationError(str(exc)) from exc
        sid = _id("edc_ser")
        record = {
            "serialization_id": sid,
            "format": format,
            "size": len(blob),
            "preview": blob[:120].decode("utf-8", errors="replace"),
            "serialized_at": _now(),
        }
        self.store.edc_serializations.save(sid, record)
        return record

    def map_dto_to_event(self, data: dict[str, Any]) -> dict[str, Any]:
        from platform_contracts.dto.base import BaseDTO

        dto = BaseDTO.from_dict({**BaseDTO().to_dict(), **data})
        event = self.library.mapping.dto_to_event(dto)
        mid = _id("edc_map")
        record = {"mapping_id": mid, "event": event.to_dict(), "mapped_at": _now()}
        self.store.edc_mappings.save(mid, record)
        return record

    def run_contract_tests(self) -> dict[str, Any]:
        dto = ContactDTO(name="Test")
        event = EntityCreatedEvent(
            aggregate_id=dto.id,
            aggregate_type="contact",
            source_service="test",
            actor="tester",
            payload=dto.to_dict(),
            trace_id="t1",
        )
        report = self.library.testing.run(dto=dto, event=event)
        tid = _id("edc_test")
        record = {"test_id": tid, **report, "run_at": _now()}
        self.store.edc_tests.save(tid, record)
        return record

    def documentation(self) -> dict[str, Any]:
        docs = self.library.docs.generate(
            dto_registry=self.library.dto_registry,
            schema_registry=self.library.schema_registry,
        )
        items = self.store.edc_docs.list_all()
        if items:
            return items[-1]
        doc_id = _id("edc_doc")
        record = {"doc_id": doc_id, **docs, "generated_at": _now()}
        self.store.edc_docs.save(doc_id, record)
        return record

    def get_schema(self, name: str, version: int | None = None) -> dict[str, Any]:
        try:
            return self.library.schema_registry.get(name, version)
        except KeyError as exc:
            raise NotFoundError(str(exc)) from exc

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.edc_bootstraps.list_all()),
            "dto_registry": len(self.store.edc_dto_registry.list_all()),
            "schemas": len(self.store.edc_schemas.list_all()),
            "tests": len(self.store.edc_tests.list_all()),
        }


data_contracts = DataContractsSuite()
