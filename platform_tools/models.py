# Tool framework domain models.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable


class ToolCategory(str, Enum):
    INTERNAL = "internal"
    REST_API = "rest_api"
    DATABASE = "database"
    TELEGRAM = "telegram"
    FILESYSTEM = "filesystem"
    EMAIL = "email"
    HTTP = "http"
    SEARCH = "search"
    CALENDAR = "calendar"
    CRM = "crm"
    PLUGIN = "plugin"


class ToolPermission(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


ToolHandler = Callable[["ToolContext", dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass
class ToolContext:
    """Runtime context for tool execution — injected, no global state."""

    agent_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    permissions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def has_permission(self, permission: ToolPermission | str) -> bool:
        perm = permission.value if isinstance(permission, ToolPermission) else permission
        if ToolPermission.ADMIN.value in self.permissions:
            return True
        return perm in self.permissions


@dataclass
class ToolResult:
    tool_id: str
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    execution_time_ms: float = 0.0
    retries: int = 0
    progress: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "success": self.success,
            "output": dict(self.output),
            "error": self.error,
            "execution_id": self.execution_id,
            "execution_time_ms": self.execution_time_ms,
            "retries": self.retries,
            "progress": self.progress,
        }


@dataclass
class Tool:
    """Universal tool definition."""

    tool_id: str
    name: str
    description: str
    category: ToolCategory
    required_permissions: list[ToolPermission] = field(default_factory=lambda: [ToolPermission.EXECUTE])
    version: str = "1.0.0"
    author: str = "Platform"
    handler: ToolHandler | None = None
    timeout_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "required_permissions": [p.value for p in self.required_permissions],
            "version": self.version,
            "author": self.author,
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }


@dataclass
class ExecutionProgress:
    execution_id: str
    tool_id: str
    progress: float = 0.0
    message: str = ""
    updated_at: float = field(default_factory=time.time)
