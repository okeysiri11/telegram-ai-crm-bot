"""Advisor integrations — Sprint 22.1."""

from __future__ import annotations

from typing import Any

from platform_ai_business_advisor.models import INTEGRATION_TARGETS


class AdvisorIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "linked": True,
            "product_intelligence_handoff": True,
        }

    def to_product_intelligence(self, recommendation: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": "ai_business_advisor",
            "title": f"Advisor recommendation: {recommendation.get('kind')}",
            "description": f"From opportunity {recommendation.get('opportunity')}",
            "module": "ai_business_advisor",
            "requires_owner_approval": True,
            "payload": recommendation,
        }
