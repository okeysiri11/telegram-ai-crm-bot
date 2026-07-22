from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


DOC_TYPES = (
    "manual",
    "engineering_wiki",
    "assembly_guide",
    "maintenance_procedure",
    "wiring_diagram",
    "firmware_note",
    "build_history",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DocumentationRecord:
    document_id: str
    title: str
    doc_type: str
    content: str = ""
    project_id: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "doc_type": self.doc_type,
            "content": self.content,
            "project_id": self.project_id,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }
