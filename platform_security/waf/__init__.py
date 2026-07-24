"""Web application firewall rules — Sprint 21.4."""

from __future__ import annotations

from typing import Any


class WafEngine:
    BLOCKED_PATTERNS = ("<script", "union select", "../", "; drop")

    def inspect(self, *, path: str = "/", body: str = "", headers: dict[str, str] | None = None) -> dict[str, Any]:
        hay = f"{path} {body}".lower()
        hits = [p for p in self.BLOCKED_PATTERNS if p in hay]
        return {
            "allowed": len(hits) == 0,
            "hits": hits,
            "headers_inspected": list((headers or {}).keys()),
        }
