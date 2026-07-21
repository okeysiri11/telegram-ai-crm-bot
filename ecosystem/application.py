# EcosystemApplication — unified identity and workspace facade.

from __future__ import annotations

from typing import Any

from ecosystem.config import DEFAULT_CONFIG, EcosystemConfig
from ecosystem.engine import EcosystemEngine, ecosystem_engine
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class EcosystemApplication:
    """Unified ecosystem layer — connects all applications on AI Platform Core v3.0."""

    def __init__(
        self,
        *,
        config: EcosystemConfig | None = None,
        store: EcosystemStore | None = None,
        engine: EcosystemEngine | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or ecosystem_store
        self.engine = engine or ecosystem_engine

    def reset(self) -> None:
        self.store.reset()

    def health(self) -> dict[str, Any]:
        return {
            "application": "ecosystem",
            "ecosystem_version": self.config.ecosystem_version,
            "platform_dependency": self.config.platform_dependency,
            "communication_layer": self.config.communication_layer,
            "event_bus": self.config.event_bus,
            "assistant_layer": self.config.assistant_layer,
            "global_knowledge": self.config.global_knowledge,
            "workforce_layer": self.config.workforce_layer,
            "executive_ai": self.config.executive_ai,
            "optimization_layer": self.config.optimization_layer,
            "continuous_learning": self.config.continuous_learning,
            "governance_layer": self.config.governance_layer,
            "compliance_layer": self.config.compliance_layer,
            "metrics": self.engine.metrics(),
        }


ecosystem = EcosystemApplication()
