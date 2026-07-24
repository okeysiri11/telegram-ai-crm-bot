"""Domain scenario builders."""

from applications.enterprise_hub.simulation_engine.scenarios.finance import FinanceScenario
from applications.enterprise_hub.simulation_engine.scenarios.logistics import LogisticsScenario
from applications.enterprise_hub.simulation_engine.scenarios.manufacturing import ManufacturingScenario
from applications.enterprise_hub.simulation_engine.scenarios.warehouse import WarehouseScenario
from applications.enterprise_hub.simulation_engine.scenarios.hr import HrScenario
from applications.enterprise_hub.simulation_engine.scenarios.procurement import ProcurementScenario
from applications.enterprise_hub.simulation_engine.scenarios.construction import ConstructionScenario
from applications.enterprise_hub.simulation_engine.scenarios.maritime import MaritimeScenario
from applications.enterprise_hub.simulation_engine.scenarios.custom import CustomScenario

__all__ = [
    "FinanceScenario",
    "LogisticsScenario",
    "ManufacturingScenario",
    "WarehouseScenario",
    "HrScenario",
    "ProcurementScenario",
    "ConstructionScenario",
    "MaritimeScenario",
    "CustomScenario",
]
