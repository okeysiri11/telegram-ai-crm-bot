"""Beauty OS library facade — Sprint 22.2."""

from __future__ import annotations

from typing import Any

from platform_beauty_os.appointments import AppointmentEngine
from platform_beauty_os.branches import BranchManagement
from platform_beauty_os.company import CompanyProfile
from platform_beauty_os.customers import CustomerProfile
from platform_beauty_os.dashboard import BeautyDashboard
from platform_beauty_os.employees import EmployeeManagement
from platform_beauty_os.integrations import BeautyIntegrations
from platform_beauty_os.models import INDUSTRY, PRINCIPLES
from platform_beauty_os.resources import ResourceManagement
from platform_beauty_os.services import ServiceCatalog


class BeautyOSLibrary:
    def __init__(self) -> None:
        self.company = CompanyProfile()
        self.branches = BranchManagement()
        self.employees = EmployeeManagement()
        self.services = ServiceCatalog()
        self.resources = ResourceManagement()
        self.customers = CustomerProfile()
        self.appointments = AppointmentEngine()
        self.dashboard = BeautyDashboard()
        self.integrations = BeautyIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        company = self.company.create(
            name="Pilot Beauty Salon",
            timezone="Europe/Moscow",
            currency="RUB",
            contacts={"phone": "+7-000-000-00-00"},
            social={"instagram": "@pilot_beauty"},
        )
        branch = self.branches.create(name="Central", address="Main St 1")
        employee = self.employees.create(
            name="Anna Master",
            role="stylist",
            specialization="hair",
            services=["Haircut"],
            commission_pct=0.45,
            salary=800.0,
        )
        catalog = self.services.seed()
        room = self.resources.create(name="Room A", kind="room", branch="Central")
        chair = self.resources.create(name="Chair 1", kind="chair", branch="Central")
        customer = self.customers.create(name="Maria Client", preferences=["quiet"], allergies=[])
        appt = self.appointments.create(
            customer_id="customer:maria",
            service_id="service:haircut",
            employee_id="employee:anna",
            branch_id="branch:central",
            start="2026-07-25T10:00:00Z",
            end="2026-07-25T10:45:00Z",
            resource_id="resource:chair1",
        )
        booking = self.resources.book(
            resource_id="resource:chair1",
            start=appt["start"],
            end=appt["end"],
            appointment_id="appt:1",
        )
        confirmed = self.appointments.transition(appt, status="confirmed")
        links = self.integrations.link()
        dash = self.dashboard.render(
            appointments=[confirmed],
            customers=[customer],
            employees=[employee],
            services=catalog,
            advisor_brief={"recommended_actions": ["launch_promotion", "winback_customers"]},
        )
        return {
            "bootstrap": True,
            "industry": INDUSTRY,
            "principles": self.principles(),
            "company": company["name"],
            "branches": 1,
            "employees": 1,
            "services": len(catalog),
            "resources": 2,
            "customers": 1,
            "appointments": 1,
            "resource_conflict_free": booking["conflict"] is False,
            "dashboard_status": dash["status"],
            "integrations_linked": links["linked"],
            "duplicates_core_logic": False,
            "pilot_ready": True,
            "status": "ready",
            "integrations": links,
            "full": {
                "company": company,
                "branch": branch,
                "employee": employee,
                "catalog": catalog,
                "resources": [room, chair],
                "customer": customer,
                "appointment": confirmed,
                "dashboard": dash,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "industry": INDUSTRY,
            "components": [
                "company",
                "branches",
                "employees",
                "services",
                "resources",
                "customers",
                "appointments",
                "dashboard",
            ],
            "principles": self.principles(),
            "resources": self.resources.status(),
        }


beauty_os_library = BeautyOSLibrary()
