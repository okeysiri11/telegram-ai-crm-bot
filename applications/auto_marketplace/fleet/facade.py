# Fleet domain facade — Sprint 10.7.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.ai_operations.engine import AIOperationsEngine, ai_operations_engine
from applications.auto_marketplace.corporate.engine import CorporateMobilityEngine, corporate_mobility_engine
from applications.auto_marketplace.dispatch.fleet_engine import FleetDispatchEngine, fleet_dispatch_engine
from applications.auto_marketplace.drivers.engine import DriverEngine, driver_engine
from applications.auto_marketplace.executive.engine import ExecutiveDashboardEngine, executive_dashboard_engine
from applications.auto_marketplace.fleet.engine import FleetEngine, fleet_engine
from applications.auto_marketplace.leasing.fleet_engine import FleetLeasingEngine, fleet_leasing_engine
from applications.auto_marketplace.mobility.engine import MobilityEngine, mobility_engine
from applications.auto_marketplace.operations.engine import OperationsEngine, operations_engine
from applications.auto_marketplace.rental.engine import RentalEngine, rental_engine
from applications.auto_marketplace.subscriptions.engine import SubscriptionEngine, subscription_engine
from applications.auto_marketplace.telematics.engine import TelematicsEngine, telematics_engine


class FleetDomainEngine:
    """Sprint 10.7 — fleet, rental, corporate mobility, AI operations."""

    def __init__(
        self,
        fleet: FleetEngine | None = None,
        rental: RentalEngine | None = None,
        leasing: FleetLeasingEngine | None = None,
        subscriptions: SubscriptionEngine | None = None,
        corporate: CorporateMobilityEngine | None = None,
        dispatch: FleetDispatchEngine | None = None,
        telematics: TelematicsEngine | None = None,
        drivers: DriverEngine | None = None,
        operations: OperationsEngine | None = None,
        executive: ExecutiveDashboardEngine | None = None,
        mobility: MobilityEngine | None = None,
        ai_operations: AIOperationsEngine | None = None,
    ) -> None:
        self.fleet = fleet or fleet_engine
        self.rental = rental or rental_engine
        self.leasing = leasing or fleet_leasing_engine
        self.subscriptions = subscriptions or subscription_engine
        self.corporate = corporate or corporate_mobility_engine
        self.dispatch = dispatch or fleet_dispatch_engine
        self.telematics = telematics or telematics_engine
        self.drivers = drivers or driver_engine
        self.operations = operations or operations_engine
        self.executive = executive or executive_dashboard_engine
        self.mobility = mobility or mobility_engine
        self.ai_operations = ai_operations or ai_operations_engine

    def metrics(self) -> dict[str, Any]:
        return {
            "fleet": self.fleet.metrics(),
            "rental": self.rental.metrics(),
            "leasing": self.leasing.metrics(),
            "subscriptions": self.subscriptions.metrics(),
            "corporate": self.corporate.metrics(),
            "dispatch": self.dispatch.metrics(),
            "telematics": self.telematics.metrics(),
            "drivers": self.drivers.metrics(),
            "operations": self.operations.metrics(),
            "executive": self.executive.metrics(),
            "ai_operations": self.ai_operations.metrics(),
        }


fleet_domain_engine = FleetDomainEngine()
