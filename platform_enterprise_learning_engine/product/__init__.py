"""Product Evolution bridge — Sprint 24.8."""

from __future__ import annotations

from typing import Any

from platform_enterprise_learning_engine.models import PRODUCT_EVOLUTION_PIPELINE


class ProductEvolution:
    def push(self, *, improvement: str, confirmed: bool = False) -> dict[str, Any]:
        if not improvement:
            raise ValueError("improvement is required")
        if not confirmed:
            raise ValueError("only confirmed improvements enter product evolution")
        return {
            "improvement": improvement,
            "pipeline": list(PRODUCT_EVOLUTION_PIPELINE),
            "stage": "product_intelligence",
            "confirmed": True,
            "requires_owner_before_dev": True,
            "auto_deploy": False,
        }
