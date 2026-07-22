# Service Center Engine — branches, mechanics, advisors, bays, queues.

from __future__ import annotations

from applications.auto_marketplace.service_centers.models import (
    Mechanic,
    RepairBay,
    ServiceAdvisor,
    ServiceCenter,
)
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class ServiceCenterEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def create_center(self, center: ServiceCenter) -> ServiceCenter:
        if not center.name:
            raise ValidationError("name is required")
        return self._store.service_centers.save(center.center_id, center)

    def get_center(self, center_id: str) -> ServiceCenter:
        center = self._store.service_centers.get(center_id)
        if center is None:
            raise NotFoundError("ServiceCenter", center_id)
        return center

    def list_centers(self) -> list[ServiceCenter]:
        return self._store.service_centers.list_all()

    def add_mechanic(self, mechanic: Mechanic) -> Mechanic:
        self.get_center(mechanic.center_id)
        return self._store.service_mechanics.save(mechanic.mechanic_id, mechanic)

    def add_advisor(self, advisor: ServiceAdvisor) -> ServiceAdvisor:
        self.get_center(advisor.center_id)
        return self._store.service_advisors.save(advisor.advisor_id, advisor)

    def add_bay(self, bay: RepairBay) -> RepairBay:
        self.get_center(bay.center_id)
        return self._store.repair_bays.save(bay.bay_id, bay)

    def enqueue(self, center_id: str, order_id: str, priority: int = 0) -> dict:
        self.get_center(center_id)
        item = {"center_id": center_id, "order_id": order_id, "priority": priority, "status": "queued"}
        self._store.service_queues.save(f"{center_id}:{order_id}", item)
        return item

    def queue(self, center_id: str) -> list[dict]:
        items = [q for q in self._store.service_queues.list_all() if q["center_id"] == center_id]
        return sorted(items, key=lambda q: (-q.get("priority", 0), q["order_id"]))

    def metrics(self) -> dict:
        return {
            "centers": self._store.service_centers.count(),
            "mechanics": self._store.service_mechanics.count(),
            "advisors": self._store.service_advisors.count(),
            "bays": self._store.repair_bays.count(),
            "queue": self._store.service_queues.count(),
        }


service_center_engine = ServiceCenterEngine()
