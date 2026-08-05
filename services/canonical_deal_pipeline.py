# Canonical Deal Pipeline entry — Sprint 32.3.
# Re-exports the SoR engine; do not add a second pipeline implementation here.

from __future__ import annotations

from typing import Any

CANONICAL_DEAL_PIPELINE = "database.models.deal_pipeline_engine"
CANONICAL_SERVICE = "services.pg_deal_pipeline_engine"


def deal_pipeline_info() -> dict[str, Any]:
    return {
        "canonical_model": CANONICAL_DEAL_PIPELINE,
        "canonical_service": CANONICAL_SERVICE,
        "entry": "services.canonical_deal_pipeline",
        "legacy": [
            "database.models.deals",
            "database.models.deal",
            "database.models.deal_engine_v1",
            "database.models.lead_engine",
            "database.models.automotive_sales",
        ],
        "policy": "New deal features extend deal_pipeline_engine / pg_deal_pipeline_engine only",
    }


def get_pipeline_engine():
    """Lazy import of the canonical PG deal pipeline engine."""
    from services.pg_deal_pipeline_engine import DealPipelineEngineV2

    return DealPipelineEngineV2


__all__ = [
    "CANONICAL_DEAL_PIPELINE",
    "CANONICAL_SERVICE",
    "deal_pipeline_info",
    "get_pipeline_engine",
]
