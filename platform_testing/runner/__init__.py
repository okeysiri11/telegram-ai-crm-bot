"""Test Runner — Sprint 25.1."""

from __future__ import annotations

from typing import Any


class TestRunner:
    def select(
        self,
        *,
        catalog: list[dict[str, Any]],
        test_id: str | None = None,
        group: list[str] | None = None,
        module: str | None = None,
        tag: str | None = None,
        changed_files: list[str] | None = None,
        full: bool = False,
    ) -> list[dict[str, Any]]:
        catalog = list(catalog or [])
        if full:
            return catalog
        if test_id:
            return [t for t in catalog if t.get("test_id") == test_id]
        if group:
            ids = set(group)
            return [t for t in catalog if t.get("test_id") in ids]
        if module:
            return [t for t in catalog if t.get("module") == module]
        if tag:
            return [t for t in catalog if tag in (t.get("tags") or [])]
        if changed_files:
            # map changed paths to modules by simple substring match
            selected = []
            for t in catalog:
                mod = t.get("module", "")
                if any(mod in f or f.endswith(mod) or mod.replace(".", "/") in f for f in changed_files):
                    selected.append(t)
            return selected or [t for t in catalog if t.get("category") == "smoke"]
        raise ValueError("specify test_id, group, module, tag, changed_files or full")

    def execute(self, *, tests: list[dict[str, Any]], fail_ids: list[str] | None = None) -> dict[str, Any]:
        fail_ids = set(fail_ids or [])
        results = []
        for t in tests:
            tid = t.get("test_id")
            status = "failed" if tid in fail_ids else "passed"
            results.append({
                "test_id": tid,
                "name": t.get("name"),
                "module": t.get("module"),
                "category": t.get("category"),
                "status": status,
                "duration_ms": int(t.get("estimated_duration_ms", 50)),
            })
        passed = sum(1 for r in results if r["status"] == "passed")
        failed = sum(1 for r in results if r["status"] == "failed")
        return {
            "results": results,
            "passed": passed,
            "failed": failed,
            "skipped": 0,
            "total": len(results),
            "success": failed == 0,
        }
