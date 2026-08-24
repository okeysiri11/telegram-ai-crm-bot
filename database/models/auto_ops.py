"""AUTO 1.0 private import/dealership persistence — additive tables."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, Boolean, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class AutoOpsVehicle(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_vehicles"
    __table_args__ = (
        UniqueConstraint("organization_id", "vin", name="uq_auto_ops_vehicles_org_vin"),
        Index("ix_auto_ops_vehicles_org", "organization_id"),
        Index("ix_auto_ops_vehicles_status", "organization_id", "status"),
        Index("ix_auto_ops_vehicles_vin", "vin"),
    )

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    vin: Mapped[str] = mapped_column(String(32), nullable=False)
    vin_nonstandard: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    workspace_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    internal_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="INTEREST")
    manufacturer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trim: Mapped[str | None] = mapped_column(String(128), nullable=True)
    body_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fuel_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    engine: Mapped[str | None] = mapped_column(String(128), nullable=True)
    transmission: Mapped[str | None] = mapped_column(String(64), nullable=True)
    drive_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    exterior_color: Mapped[str | None] = mapped_column(String(64), nullable=True)
    interior_color: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mileage: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    mileage_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    country_of_origin: Mapped[str | None] = mapped_column(String(64), nullable=True)
    purchase_country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    auction_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    auction_lot: Mapped[str | None] = mapped_column(String(64), nullable=True)
    auction_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    purchase_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    purchase_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    purchase_currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    buyer_fee: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    estimated_market_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    location_current: Mapped[str | None] = mapped_column(String(256), nullable=True)
    origin_port: Mapped[str | None] = mapped_column(String(128), nullable=True)
    destination_port: Mapped[str | None] = mapped_column(String(128), nullable=True)
    assigned_manager_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cover_photo_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sale_price_expected: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    sale_price_actual: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    sale_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sale_currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsExpense(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_expenses"
    __table_args__ = (
        Index("ix_auto_ops_expenses_org", "organization_id"),
        Index("ix_auto_ops_expenses_vehicle", "vehicle_id"),
    )

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    vehicle_id: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    exchange_rate: Mapped[Decimal | None] = mapped_column(Numeric(14, 6), nullable=True)
    amount_base_currency: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    payment_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    due_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    counterparty: Mapped[str | None] = mapped_column(String(256), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payment_status: Mapped[str] = mapped_column(String(32), nullable=False, default="paid")
    document_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    shipment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    customs_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsDocument(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_documents"
    __table_args__ = (Index("ix_auto_ops_documents_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    document_type: Mapped[str] = mapped_column(String(64), nullable=False, default="other")
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    file_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    owner_type: Mapped[str] = mapped_column(String(32), nullable=False, default="vehicle")
    vehicle_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    shipment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    customs_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    deal_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sale_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    container_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    carrier_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    driver_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    truck_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vessel_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    archived_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    previous_file_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    uploaded_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    workflow_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    signature_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    issued_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    issued_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    valid_until: Mapped[str | None] = mapped_column(String(32), nullable=True)
    finance_verify: Mapped[str | None] = mapped_column(String(32), nullable=True)
    generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    template_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ocr_draft: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    extracted_vin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str | None] = mapped_column(String(16), nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    legal_disclaimer: Mapped[str | None] = mapped_column(Text(), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsPhoto(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_photos"
    __table_args__ = (Index("ix_auto_ops_photos_vehicle", "vehicle_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    vehicle_id: Mapped[str] = mapped_column(String(64), nullable=False)
    shipment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="OTHER")
    file_id: Mapped[str] = mapped_column(String(64), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    location: Mapped[str | None] = mapped_column(String(256), nullable=True)
    captured_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_cover: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    uploaded_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsClient(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_clients"
    __table_args__ = (Index("ix_auto_ops_clients_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    telegram: Mapped[str | None] = mapped_column(String(128), nullable=True)
    email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    assigned_manager_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="lead")
    passport_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    id_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    representative: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsTask(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_tasks"
    __table_args__ = (Index("ix_auto_ops_tasks_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    vehicle_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    shipment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    customs_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    deal_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assigned_manager_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    due_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsAudit(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_audit"
    __table_args__ = (
        Index("ix_auto_ops_audit_org", "organization_id"),
        Index("ix_auto_ops_audit_entity", "entity_type", "entity_id"),
    )

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    actor_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    old_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text(), nullable=True)


class AutoOpsFile(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_files"
    __table_args__ = (Index("ix_auto_ops_files_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    uploaded_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

class AutoOpsShipment(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_shipments"
    __table_args__ = (
        Index("ix_auto_ops_shipments_org", "organization_id"),
        Index("ix_auto_ops_shipments_vehicle", "vehicle_id"),
        Index("ix_auto_ops_shipments_status", "organization_id", "status"),
    )

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    vehicle_id: Mapped[str] = mapped_column(String(64), nullable=False)
    shipment_type: Mapped[str] = mapped_column(String(32), nullable=False, default="CONTAINER")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PLANNED")
    origin_country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    origin_location: Mapped[str | None] = mapped_column(String(256), nullable=True)
    destination_country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    destination_location: Mapped[str | None] = mapped_column(String(256), nullable=True)
    pickup_address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    pickup_date_planned: Mapped[str | None] = mapped_column(String(32), nullable=True)
    pickup_date_actual: Mapped[str | None] = mapped_column(String(32), nullable=True)
    carrier_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    driver_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    truck_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    container_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vessel_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    booking_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    bill_of_lading_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tracking_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    origin_port_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    destination_port_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    etd: Mapped[str | None] = mapped_column(String(32), nullable=True)
    atd: Mapped[str | None] = mapped_column(String(32), nullable=True)
    eta: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ata: Mapped[str | None] = mapped_column(String(32), nullable=True)
    planned_eta: Mapped[str | None] = mapped_column(String(32), nullable=True)
    current_eta: Mapped[str | None] = mapped_column(String(32), nullable=True)
    eta_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    customs_handoff_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    delivery_date_planned: Mapped[str | None] = mapped_column(String(32), nullable=True)
    delivery_date_actual: Mapped[str | None] = mapped_column(String(32), nullable=True)
    responsible_manager_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    origin_lat: Mapped[str | None] = mapped_column(String(32), nullable=True)
    origin_lng: Mapped[str | None] = mapped_column(String(32), nullable=True)
    destination_lat: Mapped[str | None] = mapped_column(String(32), nullable=True)
    destination_lng: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsCarrier(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_carriers"
    __table_args__ = (Index("ix_auto_ops_carriers_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    company_name: Mapped[str] = mapped_column(String(256), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False, default="other")
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contact_person: Mapped[str | None] = mapped_column(String(256), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    telegram: Mapped[str | None] = mapped_column(String(128), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(64), nullable=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    rating: Mapped[str | None] = mapped_column(String(16), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsDriver(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_drivers"
    __table_args__ = (Index("ix_auto_ops_drivers_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    full_name: Mapped[str] = mapped_column(String(256), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    telegram: Mapped[str | None] = mapped_column(String(128), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(64), nullable=True)
    passport_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    driver_license: Mapped[str | None] = mapped_column(String(128), nullable=True)
    carrier_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    truck_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsTruck(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_trucks"
    __table_args__ = (Index("ix_auto_ops_trucks_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    type: Mapped[str] = mapped_column(String(32), nullable=False, default="truck")
    plate_number: Mapped[str] = mapped_column(String(64), nullable=False)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    vin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    carrier_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    driver_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    capacity: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsContainer(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_containers"
    __table_args__ = (
        Index("ix_auto_ops_containers_org", "organization_id"),
        UniqueConstraint("organization_id", "container_number", name="uq_auto_ops_containers_org_number"),
    )

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    container_number: Mapped[str] = mapped_column(String(32), nullable=False)
    container_type: Mapped[str] = mapped_column(String(16), nullable=False, default="40HC")
    shipping_line: Mapped[str | None] = mapped_column(String(128), nullable=True)
    booking_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    seal_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    origin_port: Mapped[str | None] = mapped_column(String(64), nullable=True)
    destination_port: Mapped[str | None] = mapped_column(String(64), nullable=True)
    etd: Mapped[str | None] = mapped_column(String(32), nullable=True)
    eta: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PLANNED")
    current_location: Mapped[str | None] = mapped_column(String(256), nullable=True)
    tracking_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    tracking_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    responsible_manager_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsContainerVehicle(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_container_vehicles"
    __table_args__ = (Index("ix_auto_ops_container_vehicles_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    container_id: Mapped[str] = mapped_column(String(64), nullable=False)
    vehicle_id: Mapped[str] = mapped_column(String(64), nullable=False)
    released_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsVessel(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_vessels"
    __table_args__ = (Index("ix_auto_ops_vessels_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    imo: Mapped[str | None] = mapped_column(String(32), nullable=True)
    mmsi: Mapped[str | None] = mapped_column(String(32), nullable=True)
    shipping_line: Mapped[str | None] = mapped_column(String(128), nullable=True)
    voyage_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    origin_port: Mapped[str | None] = mapped_column(String(64), nullable=True)
    destination_port: Mapped[str | None] = mapped_column(String(64), nullable=True)
    etd: Mapped[str | None] = mapped_column(String(32), nullable=True)
    eta: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PLANNED")
    tracking_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    position_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsPort(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_ports"
    __table_args__ = (Index("ix_auto_ops_ports_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    unlocode: Mapped[str | None] = mapped_column(String(8), nullable=True)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsLogisticsEvent(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_logistics_events"
    __table_args__ = (Index("ix_auto_ops_logistics_events_ship", "shipment_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    shipment_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    actor_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    location: Mapped[str | None] = mapped_column(String(256), nullable=True)
    document_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    photo_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsNotification(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_notifications"
    __table_args__ = (Index("ix_auto_ops_notifications_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    notification_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    shipment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vehicle_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    channel: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsLogisticsSetting(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_logistics_settings"
    __table_args__ = (Index("ix_auto_ops_logistics_settings_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    yellow_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    orange_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    default_origin_country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    default_destination_country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    default_origin_port: Mapped[str | None] = mapped_column(String(64), nullable=True)
    default_destination_port: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsCustomsCase(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_customs_cases"
    __table_args__ = (
        Index("ix_auto_ops_customs_cases_org", "organization_id"),
        Index("ix_auto_ops_customs_cases_vehicle", "vehicle_id"),
        Index("ix_auto_ops_customs_cases_status", "organization_id", "status"),
    )

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    vehicle_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DOCUMENTS_PREP")
    broker_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    customs_office: Mapped[str | None] = mapped_column(String(256), nullable=True)
    declaration_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    customs_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    fx_rate_to_uah: Mapped[Decimal | None] = mapped_column(Numeric(14, 6), nullable=True)
    engine_cc: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    fuel_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    broker_fee_uah: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    duty_uah: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    excise_uah: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    import_vat_uah: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    state_total_uah: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    grand_total_uah: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    location_current: Mapped[str | None] = mapped_column(String(256), nullable=True)
    responsible_manager_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cert_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cert_body: Mapped[str | None] = mapped_column(String(256), nullable=True)
    cert_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cert_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reg_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    plate_expected: Mapped[str | None] = mapped_column(String(32), nullable=True)
    mreo_office: Mapped[str | None] = mapped_column(String(256), nullable=True)
    mreo_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsBroker(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_brokers"
    __table_args__ = (Index("ix_auto_ops_brokers_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    company_name: Mapped[str] = mapped_column(String(256), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False, default="customs_broker")
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contact_person: Mapped[str | None] = mapped_column(String(256), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    telegram: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    rating: Mapped[str | None] = mapped_column(String(16), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsCustomsSetting(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_customs_settings"
    __table_args__ = (Index("ix_auto_ops_customs_settings_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    duty_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    vat_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsDeal(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_deals"
    __table_args__ = (
        Index("ix_auto_ops_deals_org", "organization_id"),
        Index("ix_auto_ops_deals_client", "client_id"),
        Index("ix_auto_ops_deals_vehicle", "vehicle_id"),
    )

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    client_id: Mapped[str] = mapped_column(String(64), nullable=False)
    vehicle_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default="LEAD")
    assigned_manager_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sale_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    due_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payment_due: Mapped[str | None] = mapped_column(String(32), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsReservation(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_reservations"
    __table_args__ = (Index("ix_auto_ops_reservations_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    vehicle_id: Mapped[str] = mapped_column(String(64), nullable=False)
    client_id: Mapped[str] = mapped_column(String(64), nullable=False)
    deal_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    expires_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    override_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsSale(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_sales"
    __table_args__ = (Index("ix_auto_ops_sales_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    vehicle_id: Mapped[str] = mapped_column(String(64), nullable=False)
    client_id: Mapped[str] = mapped_column(String(64), nullable=False)
    deal_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN")
    completed_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsReceipt(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_receipts"
    __table_args__ = (Index("ix_auto_ops_receipts_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    deal_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sale_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vehicle_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="PARTIAL")
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    exchange_rate: Mapped[Decimal | None] = mapped_column(Numeric(14, 6), nullable=True)
    amount_base_currency: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    confirmed_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    due_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

class AutoOpsTelegramMember(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_telegram_members"
    __table_args__ = (Index("ix_auto_ops_tg_members_org", "organization_id"), Index("ix_auto_ops_tg_members_tid", "telegram_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="auto_manager")
    username: Mapped[str | None] = mapped_column(String(128), nullable=True)
    label: Mapped[str | None] = mapped_column(String(256), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsTelegramOutbox(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_telegram_outbox"
    __table_args__ = (Index("ix_auto_ops_tg_outbox_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="event")
    text: Mapped[str | None] = mapped_column(Text(), nullable=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)




class AutoOpsStatusHistory(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_status_history"
    __table_args__ = (
        Index("ix_auto_ops_status_hist_org", "organization_id"),
        Index("ix_auto_ops_status_hist_vehicle", "organization_id", "vehicle_id"),
        Index("ix_auto_ops_status_hist_status", "organization_id", "status"),
    )

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    workspace_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    vehicle_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    entered_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    left_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str | None] = mapped_column(String(16), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class AutoOpsFinanceAccount(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_finance_accounts"
    __table_args__ = (
        Index("ix_auto_ops_fin_acct_org", "organization_id"),
        Index("ix_auto_ops_fin_acct_type", "organization_id", "account_type"),
    )

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    workspace_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False, default="OTHER")
    label: Mapped[str | None] = mapped_column(String(256), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    balance: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

class AutoOpsDocumentTemplate(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "auto_ops_document_templates"
    __table_args__ = (Index("ix_auto_ops_doc_tmpl_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False, default="other")
    stage_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    document_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    configurable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_company: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    note_ru: Mapped[str | None] = mapped_column(Text(), nullable=True)
    details: Mapped[str | None] = mapped_column(Text(), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

