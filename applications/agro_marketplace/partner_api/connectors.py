# Partner connectors — bank, insurance, logistics, government, lab, ERP, marketplace abstractions.

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.portal.models import PartnerType


class PartnerConnectors:
    """Abstraction layer for external partner systems (no Platform/Ecosystem mutation)."""

    def bank_transfer(self, *, amount: float, currency: str = "USD", reference: str = "") -> dict[str, Any]:
        return {
            "partner": PartnerType.BANK.value,
            "status": "accepted",
            "amount": amount,
            "currency": currency,
            "reference": reference or "BANK-SIM",
        }

    def insurance_quote(self, *, coverage: float, crop: str = "") -> dict[str, Any]:
        premium = round(coverage * 0.015, 2)
        return {
            "partner": PartnerType.INSURANCE.value,
            "coverage": coverage,
            "premium": premium,
            "crop": crop,
            "status": "quoted",
        }

    def logistics_book(self, *, origin: str, destination: str, tons: float = 0.0) -> dict[str, Any]:
        return {
            "partner": PartnerType.LOGISTICS.value,
            "origin": origin,
            "destination": destination,
            "tons": tons,
            "status": "booked",
            "eta_days": 14,
        }

    def government_permit(self, *, permit_type: str, country: str) -> dict[str, Any]:
        return {
            "partner": PartnerType.GOVERNMENT.value,
            "permit_type": permit_type,
            "country": country,
            "status": "submitted",
            "reference": f"GOV-{country}-{permit_type[:8].upper()}",
        }

    def laboratory_submit(self, *, sample_id: str, tests: list[str] | None = None) -> dict[str, Any]:
        return {
            "partner": PartnerType.LABORATORY.value,
            "sample_id": sample_id,
            "tests": tests or ["moisture", "aflatoxin"],
            "status": "queued",
        }

    def erp_sync(self, *, entity: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "partner": PartnerType.ERP.value,
            "entity": entity,
            "status": "synced",
            "records": 1,
            "payload_keys": list((payload or {}).keys()),
        }

    def marketplace_list(self, *, product_id: str, quantity: float, price: float) -> dict[str, Any]:
        return {
            "partner": PartnerType.MARKETPLACE.value,
            "product_id": product_id,
            "quantity": quantity,
            "price": price,
            "status": "listed",
        }


partner_connectors = PartnerConnectors()
