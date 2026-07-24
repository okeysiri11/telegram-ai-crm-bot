"""Contracts library facade — Sprint 21.3."""

from __future__ import annotations

from typing import Any

from platform_contracts.contract_testing import ContractTesting
from platform_contracts.documentation import DocumentationGenerator
from platform_contracts.dto.ai import AgentDTO
from platform_contracts.dto.base import BaseDTO
from platform_contracts.dto.crm import ContactDTO, DealDTO
from platform_contracts.dto.erp import OrderDTO
from platform_contracts.dto.maritime import VesselDTO
from platform_contracts.dto.workflow import TaskDTO, WorkflowDTO
from platform_contracts.events.base import BaseEvent
from platform_contracts.events.domain import EntityCreatedEvent
from platform_contracts.mapping import MappingEngine
from platform_contracts.models import BASE_DTO_FIELDS, DOMAINS, INTEGRATION_TARGETS
from platform_contracts.registry import DtoRegistry, SchemaRegistry
from platform_contracts.schemas import json_schema
from platform_contracts.serialization import SerializationLayer
from platform_contracts.validation import ValidationFramework
from platform_contracts.versioning import VersionCompatibility


class ContractsLibrary:
    def __init__(self) -> None:
        self.dto_registry = DtoRegistry()
        self.schema_registry = SchemaRegistry()
        self.validation = ValidationFramework()
        self.serialization = SerializationLayer()
        self.mapping = MappingEngine()
        self.versioning = VersionCompatibility()
        self.testing = ContractTesting()
        self.docs = DocumentationGenerator()

    def integrations(self) -> dict[str, Any]:
        return {"targets": list(INTEGRATION_TARGETS), "linked": True}

    def bootstrap(self) -> dict[str, Any]:
        # register domain DTOs
        samples = [
            ("ContactDTO", "crm", ContactDTO),
            ("DealDTO", "crm", DealDTO),
            ("OrderDTO", "erp", OrderDTO),
            ("WorkflowDTO", "workflow", WorkflowDTO),
            ("TaskDTO", "workflow", TaskDTO),
            ("AgentDTO", "ai", AgentDTO),
            ("VesselDTO", "maritime", VesselDTO),
            ("BaseDTO", "common", BaseDTO),
        ]
        registered = []
        for name, domain, cls in samples:
            fields = list(getattr(cls, "__dataclass_fields__", {}).keys()) or list(BASE_DTO_FIELDS)
            registered.append(self.dto_registry.register(name=name, domain=domain, fields=fields))

        # schema registry seeds
        base_schema = json_schema.sample_schema("BaseDTO")
        sch_v1 = self.schema_registry.publish(name="BaseDTO", schema=base_schema, version=1)
        sch_v2_schema = {
            **base_schema,
            "properties": {**base_schema["properties"], "tenant_id": {"type": "string"}},
        }
        compat = self.schema_registry.compatibility("BaseDTO", sch_v2_schema)
        sch_v2 = self.schema_registry.publish(name="BaseDTO", schema=sch_v2_schema, version=2)

        contact = ContactDTO(name="Ada Lovelace", tenant_id="t1", organization_id="org1")
        self.validation.validate_dto(contact)
        event = EntityCreatedEvent(
            aggregate_id=contact.id,
            aggregate_type="contact",
            source_service="crm",
            actor="bootstrap",
            payload=contact.to_dict(),
            trace_id="trace_boot",
        )
        self.validation.validate_event(event)
        mapped_event = self.mapping.dto_to_event(contact, event_type="domain.entity.created")
        entity = self.mapping.dto_to_entity(contact)
        round_dto = self.mapping.entity_to_dto(entity, dto_cls=ContactDTO)
        blob = self.serialization.serialize(contact.to_dict(), format="json")
        restored = self.serialization.deserialize(blob, format="json")
        migrated = self.versioning.migrate(contact.to_dict(), from_version=1, to_version=2)
        test_report = self.testing.run(dto=contact, event=event)
        documentation = self.docs.generate(dto_registry=self.dto_registry, schema_registry=self.schema_registry)

        return {
            "bootstrap": True,
            "domains": list(DOMAINS),
            "dtos_registered": len(registered),
            "schema_v1_id": sch_v1["schema_id"],
            "schema_v2_id": sch_v2["schema_id"],
            "schema_compatible": compat["compatible"],
            "sample_dto_id": contact.id,
            "sample_event_id": event.event_id,
            "mapped_event_id": mapped_event.event_id,
            "roundtrip_dto_id": round_dto.id,
            "serialization_formats": self.serialization.formats(),
            "json_roundtrip_ok": restored.get("id") == contact.id,
            "migrated_version": migrated["version"],
            "contract_tests_passed": test_report["passed"],
            "documentation": {
                "dto_count": len(documentation["dto_catalog"]),
                "domains": documentation["domains"],
            },
            "integrations": self.integrations(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "dto_registry": self.dto_registry.status(),
            "schema_registry": self.schema_registry.status(),
            "formats": self.serialization.formats(),
        }


contracts_library = ContractsLibrary()
