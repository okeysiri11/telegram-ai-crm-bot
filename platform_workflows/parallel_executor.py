"""Epic 45.3 — Parallel Executor for independent steps."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable

class ParallelExecutor:
    def run(self, tasks: list[tuple[str, Callable[[], Any]]], *, max_workers: int = 4) -> dict[str, Any]:
        results: dict[str, Any] = {}
        errors: dict[str, str] = {}
        if not tasks:
            return {"results": results, "errors": errors, "parallel": True}
        with ThreadPoolExecutor(max_workers=min(max_workers, len(tasks))) as pool:
            futs = {pool.submit(fn): name for name, fn in tasks}
            for fut in as_completed(futs):
                name = futs[fut]
                try:
                    results[name] = fut.result()
                except Exception as e:  # noqa: BLE001
                    errors[name] = str(e)
        return {"results": results, "errors": errors, "parallel": True, "count": len(tasks)}

parallel_executor = ParallelExecutor()
