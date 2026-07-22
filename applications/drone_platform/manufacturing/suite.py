"""Manufacturing & Production Platform facade (Sprint 11.6)."""

from __future__ import annotations

from typing import Any

from applications.drone_platform.manufacturing.assembly import AssemblyManager, assembly_manager
from applications.drone_platform.manufacturing.bom import BOMManager, bom_manager
from applications.drone_platform.manufacturing.calibration import CalibrationStation, calibration_station
from applications.drone_platform.manufacturing.flight_test import FlightTesting, flight_testing
from applications.drone_platform.manufacturing.lifecycle import LifecycleTracker, lifecycle_tracker
from applications.drone_platform.manufacturing.production import ProductionManager, production_manager
from applications.drone_platform.manufacturing.programming import ProgrammingStation, programming_station
from applications.drone_platform.manufacturing.qa import QualityAssurance, quality_assurance
from applications.drone_platform.manufacturing.service import ManufacturingService, manufacturing_service
from applications.drone_platform.manufacturing.warehouse import ComponentWarehouse, component_warehouse
from applications.drone_platform.manufacturing.workflow import ProductionWorkflow, production_workflow


class ManufacturingSuite:
    def __init__(
        self,
        builds: ManufacturingService | None = None,
        production: ProductionManager | None = None,
        assembly: AssemblyManager | None = None,
        bom: BOMManager | None = None,
        warehouse: ComponentWarehouse | None = None,
        workflow: ProductionWorkflow | None = None,
        programming: ProgrammingStation | None = None,
        calibration: CalibrationStation | None = None,
        qa: QualityAssurance | None = None,
        flight_tests: FlightTesting | None = None,
        lifecycle: LifecycleTracker | None = None,
    ) -> None:
        self.builds = builds or manufacturing_service
        self.production = production or production_manager
        self.assembly = assembly or assembly_manager
        self.bom = bom or bom_manager
        self.warehouse = warehouse or component_warehouse
        self.workflow = workflow or production_workflow
        self.programming = programming or programming_station
        self.calibration = calibration or calibration_station
        self.qa = qa or quality_assurance
        self.flight_tests = flight_tests or flight_testing
        self.lifecycle = lifecycle or lifecycle_tracker

    def status(self) -> dict[str, Any]:
        return {
            "drone_manufacturing": "1.0",
            "production": self.production.status(),
            "assembly": self.assembly.status(),
            "bom": self.bom.status(),
            "warehouse": self.warehouse.status(),
            "workflow": self.workflow.status(),
            "programming": self.programming.status(),
            "calibration": self.calibration.status(),
            "qa": self.qa.status(),
            "flight_testing": self.flight_tests.status(),
            "lifecycle": self.lifecycle.status(),
            "ready": True,
        }


manufacturing_suite = ManufacturingSuite()
