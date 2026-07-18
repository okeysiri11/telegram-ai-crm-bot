# Configuration center events — settings change notifications.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class ConfigurationChangedEvent(BaseEvent):
    config_key: str
    action: str = "set"
    section: str = ""
    old_value: Any = None
    new_value: Any = None
    version: int = 1
    changed_by: str | None = None
    reason: str | None = None
