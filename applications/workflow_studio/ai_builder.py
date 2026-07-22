"""AI Flow Builder — generate/optimize/suggest/cost/docs from prompts (Sprint 12.2)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.workflow_studio.config import DEFAULT_CONFIG
from applications.workflow_studio.editor import VisualEditor, visual_editor
from applications.workflow_studio.shared.store import WorkflowStudioStore, workflow_studio_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


PROMPT_HINTS = {
    "crm": ["webhook", "ai_agent", "condition", "notification"],
    "drone": ["scheduler", "ai_agent", "api", "decision", "notification"],
    "support": ["webhook", "llm", "condition", "human_task", "notification"],
    "finance": ["api", "condition", "approval", "database", "notification"],
}


class AIFlowBuilder:
    def __init__(self, store: WorkflowStudioStore | None = None, editor: VisualEditor | None = None) -> None:
        self.store = store or workflow_studio_store
        self.editor = editor or visual_editor

    def generate_from_prompt(self, *, prompt: str, name: str = "") -> dict[str, Any]:
        text = (prompt or "").lower()
        node_seq = ["webhook", "llm", "condition", "notification"]
        for key, seq in PROMPT_HINTS.items():
            if key in text:
                node_seq = seq
                break
        wf = self.editor.create_workflow(name=name or f"AI Flow {uuid.uuid4().hex[:6]}", description=prompt)
        created_nodes = []
        x = 0.0
        for ntype in node_seq:
            if ntype not in DEFAULT_CONFIG.node_types:
                continue
            node = self.editor.add_node(wf["workflow_id"], node_type=ntype, x=x, y=0, properties={"generated": True})
            created_nodes.append(node)
            x += 160
        for i in range(len(created_nodes) - 1):
            self.editor.connect(wf["workflow_id"], source_id=created_nodes[i]["node_id"], target_id=created_nodes[i + 1]["node_id"])
        session = {
            "session_id": f"aib_{uuid.uuid4().hex[:10]}",
            "prompt": prompt,
            "workflow_id": wf["workflow_id"],
            "nodes": [n["node_id"] for n in created_nodes],
            "at": _now(),
        }
        self.store.ai_sessions.save(session["session_id"], session)
        return {"workflow": wf, "nodes": created_nodes, "session": session}

    def optimize_workflow(self, workflow_id: str) -> dict[str, Any]:
        wf = self.editor.get_workflow(workflow_id)
        nodes = [self.store.nodes.get(nid) for nid in wf.get("node_ids", [])]
        suggestions = []
        types = [n.get("node_type") for n in nodes if n]
        if types.count("delay") > 2:
            suggestions.append("Collapse consecutive delay nodes")
        if "condition" not in types and len(types) > 3:
            suggestions.append("Add condition node for branching resilience")
        if "notification" not in types:
            suggestions.append("Add notification for failure visibility")
        return {"workflow_id": workflow_id, "suggestions": suggestions, "optimized": bool(suggestions), "at": _now()}

    def suggest_missing_nodes(self, workflow_id: str) -> dict[str, Any]:
        wf = self.editor.get_workflow(workflow_id)
        types = {(self.store.nodes.get(nid) or {}).get("node_type") for nid in wf.get("node_ids", [])}
        missing = []
        for required in ("webhook", "condition", "notification"):
            if required not in types:
                missing.append(required)
        return {"workflow_id": workflow_id, "missing": missing}

    def detect_bottlenecks(self, workflow_id: str) -> dict[str, Any]:
        wf = self.editor.get_workflow(workflow_id)
        bottlenecks = []
        for nid in wf.get("node_ids", []):
            node = self.store.nodes.get(nid)
            if not node:
                continue
            if node.get("node_type") in {"human_task", "approval", "delay"}:
                bottlenecks.append({"node_id": nid, "reason": f"{node['node_type']} may block throughput"})
        return {"workflow_id": workflow_id, "bottlenecks": bottlenecks}

    def estimate_execution_cost(self, workflow_id: str) -> dict[str, Any]:
        wf = self.editor.get_workflow(workflow_id)
        cost = 0.0
        for nid in wf.get("node_ids", []):
            node = self.store.nodes.get(nid) or {}
            ntype = node.get("node_type", "")
            cost += {"llm": 0.02, "ai_agent": 0.03, "reasoning": 0.04, "planning": 0.03}.get(ntype, 0.005)
        return {"workflow_id": workflow_id, "estimated_usd": round(cost, 4), "node_count": len(wf.get("node_ids", []))}

    def auto_documentation(self, workflow_id: str) -> dict[str, Any]:
        wf = self.editor.get_workflow(workflow_id)
        nodes = [self.store.nodes.get(nid) for nid in wf.get("node_ids", [])]
        lines = [f"# {wf['name']}", "", wf.get("description") or "Generated workflow documentation.", "", "## Nodes"]
        for node in nodes:
            if not node:
                continue
            lines.append(f"- **{node['label']}** (`{node['node_type']}`)")
        doc = "\n".join(lines)
        return {"workflow_id": workflow_id, "documentation": doc, "at": _now()}

    def status(self) -> dict[str, Any]:
        return {"ai_builder": "1.0", "sessions": len(self.store.ai_sessions.list_all()), "ready": True}


ai_flow_builder = AIFlowBuilder()
