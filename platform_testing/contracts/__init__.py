"""API Contract Engine — Sprint 25.1."""

from __future__ import annotations

from typing import Any


class APIContractEngine:
    def validate(self, *, contracts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        contracts = list(contracts or [])
        results = []
        for c in contracts:
            required = set(c.get("required_fields") or [])
            payload = set((c.get("payload") or {}).keys())
            missing = sorted(required - payload)
            results.append({
                "contract_id": c.get("contract_id", "unknown"),
                "passed": not missing,
                "missing": missing,
            })
        return {
            "engine": "api_contract",
            "results": results,
            "passed": all(r["passed"] for r in results) if results else True,
        }
