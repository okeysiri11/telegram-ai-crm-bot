"""Fallback Engine — Sprint 24.9."""

from __future__ import annotations

from typing import Any


class FallbackEngine:
    def execute(
        self,
        *,
        chain: list[dict[str, Any]],
        fail_until: int = 0,
    ) -> dict[str, Any]:
        """Simulate failover through provider chain; all switches are journaled."""
        if not chain:
            raise ValueError("fallback chain is required")
        journal: list[dict[str, Any]] = []
        for idx, hop in enumerate(chain):
            provider = hop.get("provider_id") or hop.get("name") or f"hop_{idx}"
            model = hop.get("model_id")
            failed = idx < int(fail_until)
            journal.append({
                "step": idx + 1,
                "provider_id": provider,
                "model_id": model,
                "status": "failed" if failed else "success",
                "switched": failed and idx + 1 < len(chain),
            })
            if not failed:
                return {
                    "success": True,
                    "provider_id": provider,
                    "model_id": model,
                    "journal": journal,
                    "fallback_used": idx > 0,
                    "error": False,
                }
        return {
            "success": False,
            "provider_id": None,
            "model_id": None,
            "journal": journal,
            "fallback_used": True,
            "error": True,
            "error_code": "all_providers_failed",
        }
