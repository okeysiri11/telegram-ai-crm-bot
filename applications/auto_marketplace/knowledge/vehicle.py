# Vehicle Knowledge Engine — specs, problems, recalls, maintenance, reliability.

from __future__ import annotations

from applications.auto_marketplace.ai.models import VehicleKnowledgeCard
from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class VehicleKnowledgeEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def upsert(self, card: VehicleKnowledgeCard) -> VehicleKnowledgeCard:
        if not card.make or not card.model:
            raise ValidationError("make and model are required")
        key = f"{card.make.lower()}:{card.model.lower()}:{card.year}"
        return self._store.vehicle_knowledge_cards.save(key, card)

    def get(self, make: str, model: str, year: int = 0) -> VehicleKnowledgeCard | None:
        key = f"{make.lower()}:{model.lower()}:{year}"
        card = self._store.vehicle_knowledge_cards.get(key)
        if card:
            return card
        # fallback any year
        for item in self._store.vehicle_knowledge_cards.list_all():
            if item.make.lower() == make.lower() and item.model.lower() == model.lower():
                return item
        return None

    def ensure_default(self, make: str, model: str, year: int = 2020) -> VehicleKnowledgeCard:
        existing = self.get(make, model, year)
        if existing:
            return existing
        return self.upsert(
            VehicleKnowledgeCard(
                make=make,
                model=model,
                year=year,
                specifications={"drivetrain": "fwd", "seats": 5},
                common_problems=["battery aging", "suspension wear"],
                recalls=["Airbag inspection campaign"],
                maintenance_schedule=[
                    {"km": 10000, "service": "oil_filter"},
                    {"km": 40000, "service": "brake_fluid"},
                ],
                reliability_rating=7.5,
                fuel_consumption_l_100km=7.2,
                service_intervals_km=10000,
            )
        )

    def metrics(self) -> dict:
        return {"knowledge_cards": self._store.vehicle_knowledge_cards.count()}


vehicle_knowledge_engine = VehicleKnowledgeEngine()
