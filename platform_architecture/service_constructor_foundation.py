# Universal Service Constructor foundation — Sprint 32.2.
# Architecture only (no UI). Maps to ServiceListing / marketplace contracts.

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ServiceBlueprint:
    service_id: str
    name: str
    vertical: str
    package_ids: list[str] = field(default_factory=list)
    workflow_ids: list[str] = field(default_factory=list)
    pricing_plan_id: str | None = None
    ai_agent_roles: list[str] = field(default_factory=list)
    document_types: list[str] = field(default_factory=list)
    crm_objects: list[str] = field(default_factory=list)
    marketplace_listed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ServicePackage:
    package_id: str
    name: str
    includes: list[str]


class UniversalServiceConstructorFoundation:
    """
    Future constructor building blocks:
    Service · Package · Workflow · Pricing · AI · Documents · CRM · Marketplace

    Does not implement UI. Does not replace vertical catalogs.
    """

    def __init__(self) -> None:
        self.packages: dict[str, ServicePackage] = {
            "pkg_core": ServicePackage("pkg_core", "Core Ops", ["crm", "docs", "workflow"]),
            "pkg_ai": ServicePackage("pkg_ai", "AI Assist", ["agents", "prompts"]),
            "pkg_commerce": ServicePackage("pkg_commerce", "Commerce", ["pricing", "marketplace"]),
        }
        self.blueprints: dict[str, ServiceBlueprint] = {
            "svc_auto_listing": ServiceBlueprint(
                service_id="svc_auto_listing",
                name="Auto Listing Service",
                vertical="auto",
                package_ids=["pkg_core", "pkg_commerce"],
                workflow_ids=["wf_listing_publish"],
                pricing_plan_id="growth",
                ai_agent_roles=["sales", "marketing"],
                document_types=["listing", "contract"],
                crm_objects=["lead", "deal"],
                marketplace_listed=True,
            )
        }

    def list_packages(self) -> list[dict[str, Any]]:
        return [asdict(p) for p in self.packages.values()]

    def list_blueprints(self) -> list[dict[str, Any]]:
        return [b.to_dict() for b in self.blueprints.values()]

    def compose(self, service_id: str) -> dict[str, Any]:
        bp = self.blueprints.get(service_id)
        if not bp:
            raise ValueError(f"unknown service blueprint: {service_id}")
        packages = [asdict(self.packages[pid]) for pid in bp.package_ids if pid in self.packages]
        return {
            "blueprint": bp.to_dict(),
            "packages": packages,
            "layers": {
                "domain": True,
                "service": True,
                "workflow": True,
                "pricing": True,
                "ai": True,
                "documents": True,
                "crm": True,
                "marketplace": True,
                "presentation_ui": False,
            },
            "ui_implemented": False,
            "system_of_record": "platform_service_builder",
            "note": "Sprint 36.0 productizes service install/lifecycle in platform_service_builder",
        }

    def capabilities(self) -> dict[str, Any]:
        return {
            "service": True,
            "package": True,
            "workflow": True,
            "pricing": True,
            "ai": True,
            "documents": True,
            "crm": True,
            "marketplace": True,
            "ui": False,
            "foundation_only": True,
        }


universal_service_constructor = UniversalServiceConstructorFoundation()
