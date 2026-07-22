# Sprint 9.4 — Customs / trade / documentation events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class CustomsDeclarationCreatedEvent(BaseEvent):
    declaration_id: str = ""
    procedure: str = ""
    cargo_id: str = ""
    shipment_id: str = ""


@dataclass(kw_only=True)
class CustomsReleasedEvent(BaseEvent):
    declaration_id: str = ""
    cargo_id: str = ""
    channel: str = ""


@dataclass(kw_only=True)
class CustomsInspectionStartedEvent(BaseEvent):
    inspection_id: str = ""
    declaration_id: str = ""
    cargo_id: str = ""
    inspection_type: str = ""


@dataclass(kw_only=True)
class CargoHeldEvent(BaseEvent):
    declaration_id: str = ""
    cargo_id: str = ""
    reason: str = ""


@dataclass(kw_only=True)
class CargoReleasedEvent(BaseEvent):
    declaration_id: str = ""
    cargo_id: str = ""


@dataclass(kw_only=True)
class CertificateIssuedEvent(BaseEvent):
    certificate_id: str = ""
    certificate_type: str = ""
    cargo_id: str = ""


@dataclass(kw_only=True)
class DocumentSignedEvent(BaseEvent):
    document_id: str = ""
    document_type: str = ""
    signed_by: str = ""


@dataclass(kw_only=True)
class ExportCompletedEvent(BaseEvent):
    shipment_id: str = ""
    cargo_id: str = ""
    declaration_id: str = ""


@dataclass(kw_only=True)
class ImportCompletedEvent(BaseEvent):
    shipment_id: str = ""
    cargo_id: str = ""
    declaration_id: str = ""
