# Platform Management API — orchestration layer for Admin Studio / CLI / SaaS control panel.

from platform_management.management_router import register_management_routes
from platform_management.management_service import management_service
from platform_management.permissions import ManagementRole

__all__ = [
    "management_service",
    "ManagementRole",
    "register_management_routes",
]
