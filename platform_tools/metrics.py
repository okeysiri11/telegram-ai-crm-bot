# Tool execution metrics.

from __future__ import annotations

import time
from dataclasses import dataclass, field

from platform_tools.models import ToolResult


@dataclass
class ToolMetricEntry:
    tool_id: str
    success: bool
    execution_time_ms: float
    timestamp: float = field(default_factory=time.time)


class ToolMetrics:
    def __init__(self) -> None:
        self._entries: list[ToolMetricEntry] = []

    def reset(self) -> None:
        self._entries.clear()

    def record(self, result: ToolResult) -> None:
        self._entries.append(
            ToolMetricEntry(
                tool_id=result.tool_id,
                success=result.success,
                execution_time_ms=result.execution_time_ms,
            )
        )

    def for_tool(self, tool_id: str) -> dict:
        entries = [e for e in self._entries if e.tool_id == tool_id]
        if not entries:
            return {
                "tool_id": tool_id,
                "usage_count": 0,
                "error_rate": 0.0,
                "avg_execution_time_ms": 0.0,
            }
        failures = sum(1 for e in entries if not e.success)
        return {
            "tool_id": tool_id,
            "usage_count": len(entries),
            "error_rate": round(failures / len(entries), 4),
            "avg_execution_time_ms": round(sum(e.execution_time_ms for e in entries) / len(entries), 2),
        }

    def summary(self) -> dict:
        total = len(self._entries)
        if total == 0:
            return {
                "executions": 0,
                "success_rate": 0.0,
                "error_rate": 0.0,
                "avg_execution_time_ms": 0.0,
                "unique_tools": 0,
            }
        successes = sum(1 for e in self._entries if e.success)
        tool_ids = {e.tool_id for e in self._entries}
        return {
            "executions": total,
            "success_rate": round(successes / total, 4),
            "error_rate": round((total - successes) / total, 4),
            "avg_execution_time_ms": round(sum(e.execution_time_ms for e in self._entries) / total, 2),
            "unique_tools": len(tool_ids),
            "by_tool": {tid: self.for_tool(tid) for tid in sorted(tool_ids)},
        }


tool_metrics = ToolMetrics()
