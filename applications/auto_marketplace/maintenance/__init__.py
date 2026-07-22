from applications.auto_marketplace.maintenance.service import MaintenanceService, maintenance_service

__all__ = [
    "MaintenanceService",
    "maintenance_service",
    "VehicleMaintenanceEngine",
    "vehicle_maintenance_engine",
]


def __getattr__(name: str):
    if name in {"VehicleMaintenanceEngine", "vehicle_maintenance_engine"}:
        from applications.auto_marketplace.maintenance.engine import (
            VehicleMaintenanceEngine,
            vehicle_maintenance_engine,
        )

        return VehicleMaintenanceEngine if name == "VehicleMaintenanceEngine" else vehicle_maintenance_engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
