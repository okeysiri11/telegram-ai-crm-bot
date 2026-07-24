from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"



from applications.enterprise_hub.digital_twin.prediction_context import PredictionContext
from applications.enterprise_hub.digital_twin.relationship_manager import RelationshipManager
from applications.enterprise_hub.digital_twin.snapshot_manager import SnapshotManager
from applications.enterprise_hub.digital_twin.state_manager import StateManager
from applications.enterprise_hub.digital_twin.timeline import TimelineEngine
from applications.enterprise_hub.digital_twin.twin_engine import TwinEngine
from applications.enterprise_hub.digital_twin.twin_registry import TwinRegistry
from applications.enterprise_hub.digital_twin.visualization import VisualizationLayer


class TwinManager:
    """High-level orchestration for Digital Twin operations."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = TwinRegistry(self.store)
        self.engine = TwinEngine(self.store)
        self.states = StateManager(self.store)
        self.relationships = RelationshipManager(self.store)
        self.timeline = TimelineEngine(self.store)
        self.snapshots = SnapshotManager(self.store)
        self.predictions = PredictionContext(self.store)
        self.visualization = VisualizationLayer(self.store)

    def status(self) -> dict[str, Any]:
        return {
            "registry": self.registry.status(),
            "engine": self.engine.status(),
            "relationships": self.relationships.status(),
            "timeline": self.timeline.status(),
            "snapshots": self.snapshots.status(),
        }
