"""Diagram catalog — Sprint 21.6."""

from __future__ import annotations

from typing import Any


class DiagramCatalog:
    def list_all(self) -> list[dict[str, Any]]:
        return [
            {"diagram_id": "diag_component", "type": "component", "title": "Hub Components"},
            {"diagram_id": "diag_sequence", "type": "sequence", "title": "Request Flow"},
            {"diagram_id": "diag_deploy", "type": "deployment", "title": "K8s Topology"},
        ]
