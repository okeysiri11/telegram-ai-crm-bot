# Driver Management — profiles, licenses, training, ratings, violations, hours.

from __future__ import annotations

import time

from applications.auto_marketplace.fleet.models import FleetDriver
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class DriverEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def register(self, driver: FleetDriver) -> FleetDriver:
        if not driver.name:
            raise ValidationError("name is required")
        if not driver.license_expires_at:
            driver.license_expires_at = time.time() + 2 * 365 * 86400
        return self._store.fleet_drivers.save(driver.driver_id, driver)

    def get(self, driver_id: str) -> FleetDriver:
        item = self._store.fleet_drivers.get(driver_id)
        if item is None:
            raise NotFoundError("FleetDriver", driver_id)
        return item

    def add_training(self, driver_id: str, course: str) -> FleetDriver:
        driver = self.get(driver_id)
        driver.training.append(course)
        driver.performance_score = min(100.0, driver.performance_score + 2)
        return self._store.fleet_drivers.save(driver_id, driver)

    def rate(self, driver_id: str, score: float) -> FleetDriver:
        if not 0 <= score <= 5:
            raise ValidationError("rating must be 0-5")
        driver = self.get(driver_id)
        driver.rating = score if driver.rating <= 0 else round((driver.rating + score) / 2, 2)
        return self._store.fleet_drivers.save(driver_id, driver)

    def add_violation(self, driver_id: str, description: str) -> FleetDriver:
        driver = self.get(driver_id)
        driver.violations.append({"description": description, "at": time.time()})
        driver.performance_score = max(0.0, driver.performance_score - 5)
        return self._store.fleet_drivers.save(driver_id, driver)

    def log_hours(self, driver_id: str, hours: float) -> FleetDriver:
        driver = self.get(driver_id)
        driver.hours_worked = round(driver.hours_worked + hours, 2)
        return self._store.fleet_drivers.save(driver_id, driver)

    def list_drivers(self, *, active_only: bool = True) -> list[FleetDriver]:
        items = self._store.fleet_drivers.list_all()
        if active_only:
            items = [d for d in items if d.active]
        return items

    def recommend(self, *, min_rating: float = 3.5) -> list[FleetDriver]:
        return sorted(
            [d for d in self.list_drivers() if d.rating >= min_rating or d.rating == 0],
            key=lambda d: (-d.performance_score, -d.rating),
        )

    def metrics(self) -> dict:
        return {"drivers": self._store.fleet_drivers.count()}


driver_engine = DriverEngine()
