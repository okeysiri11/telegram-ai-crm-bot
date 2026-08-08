"""Epic 45.3 — Workflow Builder (JSON graph from plan / blocks)."""
from __future__ import annotations
from typing import Any
from platform_workflows.planner import ai_planner
from platform_workflows.ua_store import WorkflowSpec, new_id, ua_store
from platform_workflows.workflow_templates import BLOCK_TYPES, get_template

class WorkflowBuilder:
    def blocks_from_plan(self, plan: dict[str, Any]) -> list[dict[str, Any]]:
        blocks = [{"id": "start", "type": "start", "title": "Начало"}]
        for step in plan.get("steps") or []:
            kind = step.get("kind") or "ai"
            btype = kind if kind in BLOCK_TYPES else ("generation" if kind == "generation" else "ai")
            if kind == "finish":
                btype = "finish"
            blocks.append({
                "id": step.get("id") or new_id("b"),
                "type": btype,
                "title": step.get("title") or step.get("id"),
                "kind": kind,
                "parallel_group": step.get("parallel_group"),
            })
        if blocks[-1]["type"] != "finish":
            blocks.append({"id": "finish", "type": "finish", "title": "Finish"})
        return blocks
    def build_from_goal(self, owner_id: str, goal_text: str, *, vertical: str = "company", channel: str = "web", template_id: str | None = None) -> dict[str, Any]:
        if template_id:
            tpl = get_template(template_id)
            if tpl:
                vertical = tpl.get("vertical") or vertical
                goal_text = tpl.get("title_ru") or goal_text
        plan = ai_planner.plan(goal_text, vertical=vertical)
        blocks = self.blocks_from_plan(plan)
        wid = new_id("wf")
        spec = WorkflowSpec(
            id=wid, owner_id=owner_id, title=goal_text[:120], blocks=blocks,
            vertical=vertical, template_id=template_id, channel=channel,
            json_def={"version": "45.3", "plan": plan, "blocks": blocks},
        )
        ua_store.workflows[wid] = spec
        return spec.to_dict()
    def create_custom(self, owner_id: str, title: str, blocks: list[dict[str, Any]], *, channel: str = "web", vertical: str = "company") -> dict[str, Any]:
        # normalize
        norm = []
        for b in blocks:
            t = b.get("type") or "ai"
            if t not in BLOCK_TYPES:
                t = "ai"
            norm.append({**b, "type": t, "id": b.get("id") or new_id("b")})
        if not norm or norm[0]["type"] != "start":
            norm.insert(0, {"id": "start", "type": "start", "title": "Начало"})
        if norm[-1]["type"] != "finish":
            norm.append({"id": "finish", "type": "finish", "title": "Finish"})
        wid = new_id("wf")
        spec = WorkflowSpec(id=wid, owner_id=owner_id, title=title, blocks=norm, vertical=vertical, channel=channel,
                            json_def={"version": "45.3", "blocks": norm})
        ua_store.workflows[wid] = spec
        return spec.to_dict()
    def clone(self, owner_id: str, workflow_id: str) -> dict[str, Any] | None:
        src = ua_store.workflows.get(workflow_id)
        if not src or src.owner_id != owner_id:
            return None
        return self.create_custom(owner_id, f"{src.title} (копия)", list(src.blocks), channel=src.channel, vertical=src.vertical)

workflow_builder = WorkflowBuilder()
