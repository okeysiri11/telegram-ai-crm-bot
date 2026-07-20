# Tool validation.

from __future__ import annotations

import re

from platform_tools.exceptions import ToolValidationError
from platform_tools.models import Tool, ToolCategory

TOOL_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(-[\w.]+)?(\+[\w.]+)?$")


def validate_tool_id(tool_id: str) -> None:
    if not tool_id or not TOOL_ID_PATTERN.match(tool_id):
        raise ToolValidationError(f"Invalid tool id '{tool_id}' — must match ^[a-z][a-z0-9_-]*$")


def validate_tool(tool: Tool) -> None:
    if not tool.name.strip():
        raise ToolValidationError("Tool name is required")
    if not tool.description.strip():
        raise ToolValidationError("Tool description is required")
    validate_tool_id(tool.tool_id)
    if not tool.version or not SEMVER_PATTERN.match(tool.version):
        raise ToolValidationError(f"Invalid version '{tool.version}'")
    if not isinstance(tool.category, ToolCategory):
        raise ToolValidationError("Tool category must be a ToolCategory enum")
    if tool.handler is None:
        raise ToolValidationError(f"Tool {tool.tool_id} must have a handler")
    if not tool.required_permissions:
        raise ToolValidationError("Tool must declare at least one required permission")
