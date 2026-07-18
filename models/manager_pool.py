# Manager pool domain types and assignment modes.

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any


class AssignmentMode(str, enum.Enum):
    ROUND_ROBIN = "ROUND_ROBIN"
    LEAST_LOADED = "LEAST_LOADED"
    WEIGHTED = "WEIGHTED"
    PRIORITY = "PRIORITY"


@dataclass(frozen=True)
class ManagerPoolSnapshot:
    id: str
    telegram_id: int
    name: str
    vertical: str
    priority: int
    weight: int
    is_active: bool
    current_load: int
    last_assigned_at: datetime | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "name": self.name,
            "vertical": self.vertical,
            "priority": self.priority,
            "weight": self.weight,
            "is_active": self.is_active,
            "current_load": self.current_load,
            "last_assigned_at": self.last_assigned_at.isoformat() if self.last_assigned_at else None,
        }
