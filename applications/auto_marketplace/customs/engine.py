# Customs Engine — declarations, brokers, VIN validation, clearance.

from __future__ import annotations

import time

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transport.models import CustomsDeclaration


class CustomsEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def create(self, declaration: CustomsDeclaration) -> CustomsDeclaration:
        if not declaration.shipment_id:
            raise ValidationError("shipment_id is required")
        declaration.vin_valid = self.validate_vin(declaration.vin)
        declaration.history.append({"event": "created", "at": time.time()})
        return self._store.customs_declarations.save(declaration.customs_id, declaration)

    def get(self, customs_id: str) -> CustomsDeclaration:
        item = self._store.customs_declarations.get(customs_id)
        if item is None:
            raise NotFoundError("CustomsDeclaration", customs_id)
        return item

    def validate_vin(self, vin: str) -> bool:
        vin = (vin or "").strip().upper()
        return len(vin) == 17 and vin.isalnum()

    def assign_broker(self, customs_id: str, *, broker_id: str, broker_name: str) -> CustomsDeclaration:
        item = self.get(customs_id)
        item.broker_id = broker_id
        item.broker_name = broker_name
        item.history.append({"event": "broker_assigned", "broker_id": broker_id, "at": time.time()})
        return self._store.customs_declarations.save(customs_id, item)

    def submit(self, customs_id: str, *, checkpoint: str = "") -> CustomsDeclaration:
        item = self.get(customs_id)
        if not item.vin_valid:
            raise ValidationError("VIN customs validation failed")
        item.checkpoint = checkpoint or item.checkpoint
        item.status = "submitted"
        item.documents.append(f"e-customs-{customs_id[:8]}")
        item.history.append({"event": "submitted", "checkpoint": item.checkpoint, "at": time.time()})
        return self._store.customs_declarations.save(customs_id, item)

    def clear(self, customs_id: str) -> CustomsDeclaration:
        item = self.get(customs_id)
        item.status = "cleared"
        item.history.append({"event": "cleared", "at": time.time()})
        return self._store.customs_declarations.save(customs_id, item)

    def hold(self, customs_id: str, reason: str = "") -> CustomsDeclaration:
        item = self.get(customs_id)
        item.status = "held"
        item.history.append({"event": "held", "reason": reason, "at": time.time()})
        return self._store.customs_declarations.save(customs_id, item)

    def assistant_advice(self, customs_id: str) -> dict:
        item = self.get(customs_id)
        tips = []
        if not item.vin_valid:
            tips.append("Provide a valid 17-character VIN")
        if not item.broker_id:
            tips.append("Assign a licensed customs broker")
        if item.status == "draft":
            tips.append("Submit electronic customs declaration before border arrival")
        if not tips:
            tips.append("Documents look complete — proceed to clearance")
        return {"customs_id": customs_id, "status": item.status, "ai_advice": tips}

    def metrics(self) -> dict:
        items = self._store.customs_declarations.list_all()
        return {
            "declarations": len(items),
            "cleared": len([d for d in items if d.status == "cleared"]),
            "held": len([d for d in items if d.status == "held"]),
        }


customs_engine = CustomsEngine()
