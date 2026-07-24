"""Digital Twin entity factories."""

from applications.enterprise_hub.digital_twin.entities.organization import OrganizationTwin
from applications.enterprise_hub.digital_twin.entities.department import DepartmentTwin
from applications.enterprise_hub.digital_twin.entities.employee import EmployeeTwin
from applications.enterprise_hub.digital_twin.entities.customer import CustomerTwin
from applications.enterprise_hub.digital_twin.entities.supplier import SupplierTwin
from applications.enterprise_hub.digital_twin.entities.project import ProjectTwin
from applications.enterprise_hub.digital_twin.entities.warehouse import WarehouseTwin
from applications.enterprise_hub.digital_twin.entities.equipment import EquipmentTwin
from applications.enterprise_hub.digital_twin.entities.vehicle import VehicleTwin
from applications.enterprise_hub.digital_twin.entities.vessel import VesselTwin
from applications.enterprise_hub.digital_twin.entities.production import ProductionTwin
from applications.enterprise_hub.digital_twin.entities.asset import AssetTwin
from applications.enterprise_hub.digital_twin.entities.ai_agent import AiAgentTwin
from applications.enterprise_hub.digital_twin.entities.custom import CustomTwin

__all__ = [
    "OrganizationTwin",
    "DepartmentTwin",
    "EmployeeTwin",
    "CustomerTwin",
    "SupplierTwin",
    "ProjectTwin",
    "WarehouseTwin",
    "EquipmentTwin",
    "VehicleTwin",
    "VesselTwin",
    "ProductionTwin",
    "AssetTwin",
    "AiAgentTwin",
    "CustomTwin",
]
