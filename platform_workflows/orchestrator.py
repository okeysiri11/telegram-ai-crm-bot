"""Epic 45.3 — Orchestrator: DAG, deps, parallel groups, recover."""
from __future__ import annotations
from typing import Any
from platform_workflows.parallel_executor import parallel_executor

class WorkflowOrchestrator:
    def build_dag(self, blocks: list[dict[str, Any]]) -> dict[str, Any]:
        nodes = [b["id"] for b in blocks]
        edges = []
        for i in range(len(blocks) - 1):
            a, b = blocks[i], blocks[i + 1]
            # sequential default unless same parallel group
            if a.get("parallel_group") and a.get("parallel_group") == b.get("parallel_group"):
                continue
            edges.append([a["id"], b["id"]])
        # connect parallel group to next sequential
        groups: dict[str, list[str]] = {}
        for b in blocks:
            g = b.get("parallel_group")
            if g:
                groups.setdefault(g, []).append(b["id"])
        return {"nodes": nodes, "edges": edges, "parallel_groups": groups}
    def merge_duplicates(self, blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        out = []
        for b in blocks:
            key = f"{b.get('type')}:{b.get('title')}"
            if key in seen and b.get("type") not in ("start", "finish"):
                continue
            seen.add(key)
            out.append(b)
        return out
    def schedule_waves(self, blocks: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
        waves: list[list[dict[str, Any]]] = []
        i = 0
        while i < len(blocks):
            b = blocks[i]
            g = b.get("parallel_group")
            if g:
                wave = []
                while i < len(blocks) and blocks[i].get("parallel_group") == g:
                    wave.append(blocks[i]); i += 1
                waves.append(wave)
            else:
                waves.append([b]); i += 1
        return waves
    def run_wave(self, wave: list[dict[str, Any]], executor_fn) -> dict[str, Any]:
        if len(wave) == 1:
            b = wave[0]
            return {"results": {b["id"]: executor_fn(b)}, "errors": {}, "parallel": False}
        tasks = [(b["id"], (lambda bb=b: executor_fn(bb))) for b in wave]
        return parallel_executor.run(tasks)

workflow_orchestrator = WorkflowOrchestrator()
