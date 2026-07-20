# Support guide and contact information.

from __future__ import annotations

from typing import Any


class SupportService:
    def guide(self) -> dict[str, Any]:
        return {
            "channels": [
                {"channel": "email", "address": "support@auto-marketplace.example", "hours": "24/7"},
                {"channel": "portal", "url": "/api/auto/v1/portal/customer/assistant", "hours": "24/7 AI"},
            ],
            "escalation": [
                {"level": 1, "team": "Customer Support", "response_sla_hours": 4},
                {"level": 2, "team": "Technical Support", "response_sla_hours": 2},
                {"level": 3, "team": "Engineering On-Call", "response_sla_hours": 1},
            ],
            "common_issues": [
                {"issue": "Login failure", "resolution": "Reset password via /portal/auth/login"},
                {"issue": "Payment not captured", "resolution": "Check /finance/payments status"},
                {"issue": "Vehicle not visible", "resolution": "Verify catalog publish via dealer portal"},
            ],
        }

    def administrator_guide(self) -> dict[str, Any]:
        return {
            "sections": [
                "User management via portal authentication",
                "CRM configuration via /api/auto/v1/crm",
                "Finance operations via /api/auto/v1/finance",
                "BI dashboards via /api/auto/v1/bi",
                "Production ops via /api/auto/v1/ops",
            ],
            "maintenance": "Use maintenance mode before upgrades",
            "monitoring": "Health at /api/auto/v1/health and /api/auto/v1/ops/health",
        }

    def user_guide(self) -> dict[str, Any]:
        return {
            "customer": [
                "Register at /portal/auth/register",
                "Search vehicles at /portal/customer/search",
                "Save favorites and book test drives",
                "Use AI assistant for help",
            ],
            "dealer": [
                "Access dashboard at /portal/dealer/dashboard",
                "Manage inventory and leads",
                "Track sales and financial overview",
            ],
        }


support_service = SupportService()
