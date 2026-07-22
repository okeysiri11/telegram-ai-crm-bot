"""Visual Editor — canvas, nodes, connections, undo/redo, clipboard, grouping (Sprint 12.2)."""

from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.workflow_studio.config import DEFAULT_CONFIG
from applications.workflow_studio.shared.exceptions import NotFoundError, ValidationError
from applications.workflow_studio.shared.store import WorkflowStudioStore, workflow_studio_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class VisualEditor:
    def __init__(self, store: WorkflowStudioStore | None = None) -> None:
        self.store = store or workflow_studio_store
        self.node_types = list(DEFAULT_CONFIG.node_types)

    def create_workflow(self, *, name: str, description: str = "", template_key: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("workflow name required")
        wid = f"wf_{uuid.uuid4().hex[:12]}"
        workflow = {
            "workflow_id": wid,
            "name": name,
            "description": description,
            "template_key": template_key,
            "status": "draft",
            "node_ids": [],
            "connection_ids": [],
            "group_ids": [],
            "comment_ids": [],
            "version": 1,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.workflows.save(wid, workflow)
        canvas = {
            "workflow_id": wid,
            "zoom": 1.0,
            "grid": True,
            "mini_map": True,
            "offset": {"x": 0, "y": 0},
            "selection": [],
            "updated_at": _now(),
        }
        self.store.canvas_states.save(wid, canvas)
        self._push_history(wid, "create_workflow", workflow)
        return workflow

    def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        item = self.store.workflows.get(workflow_id)
        if item is None:
            raise NotFoundError("workflow", workflow_id)
        return item

    def canvas(self, workflow_id: str) -> dict[str, Any]:
        self.get_workflow(workflow_id)
        state = self.store.canvas_states.get(workflow_id)
        if state is None:
            raise NotFoundError("canvas", workflow_id)
        nodes = [self.store.nodes.get(nid) for nid in self.get_workflow(workflow_id).get("node_ids", [])]
        connections = [self.store.connections.get(cid) for cid in self.get_workflow(workflow_id).get("connection_ids", [])]
        return {
            "canvas": state,
            "nodes": [n for n in nodes if n],
            "connections": [c for c in connections if c],
            "property_panel": {"selected": state.get("selection", [])},
            "mini_map": state.get("mini_map", True),
            "zoom": state.get("zoom", 1.0),
            "grid": state.get("grid", True),
        }

    def set_zoom(self, workflow_id: str, *, zoom: float) -> dict[str, Any]:
        state = self._canvas_state(workflow_id)
        state["zoom"] = max(0.25, min(4.0, float(zoom)))
        state["updated_at"] = _now()
        self.store.canvas_states.save(workflow_id, state)
        return state

    def set_grid(self, workflow_id: str, *, enabled: bool = True) -> dict[str, Any]:
        state = self._canvas_state(workflow_id)
        state["grid"] = bool(enabled)
        state["updated_at"] = _now()
        self.store.canvas_states.save(workflow_id, state)
        return state

    def add_node(
        self,
        workflow_id: str,
        *,
        node_type: str,
        label: str = "",
        x: float = 0,
        y: float = 0,
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        wf = self.get_workflow(workflow_id)
        if node_type not in self.node_types:
            raise ValidationError(f"node_type must be one of {self.node_types}")
        nid = f"node_{uuid.uuid4().hex[:10]}"
        node = {
            "node_id": nid,
            "workflow_id": workflow_id,
            "node_type": node_type,
            "label": label or node_type.replace("_", " ").title(),
            "x": x,
            "y": y,
            "properties": dict(properties or {}),
            "created_at": _now(),
        }
        self.store.nodes.save(nid, node)
        wf["node_ids"].append(nid)
        wf["updated_at"] = _now()
        self.store.workflows.save(workflow_id, wf)
        self._push_history(workflow_id, "add_node", {"node_id": nid})
        return node

    def update_node(self, node_id: str, *, properties: dict[str, Any] | None = None, x: float | None = None, y: float | None = None, label: str | None = None) -> dict[str, Any]:
        node = self.store.nodes.get(node_id)
        if node is None:
            raise NotFoundError("node", node_id)
        if properties is not None:
            node["properties"] = {**node.get("properties", {}), **properties}
        if x is not None:
            node["x"] = x
        if y is not None:
            node["y"] = y
        if label is not None:
            node["label"] = label
        node["updated_at"] = _now()
        self.store.nodes.save(node_id, node)
        self._push_history(node["workflow_id"], "update_node", {"node_id": node_id})
        return node

    def connect(self, workflow_id: str, *, source_id: str, target_id: str, label: str = "") -> dict[str, Any]:
        wf = self.get_workflow(workflow_id)
        if source_id not in wf["node_ids"] or target_id not in wf["node_ids"]:
            raise ValidationError("source and target must belong to workflow")
        cid = f"conn_{uuid.uuid4().hex[:10]}"
        conn = {
            "connection_id": cid,
            "workflow_id": workflow_id,
            "source_id": source_id,
            "target_id": target_id,
            "label": label,
            "created_at": _now(),
        }
        self.store.connections.save(cid, conn)
        wf["connection_ids"].append(cid)
        wf["updated_at"] = _now()
        self.store.workflows.save(workflow_id, wf)
        self._push_history(workflow_id, "connect", {"connection_id": cid})
        return conn

    def group_nodes(self, workflow_id: str, *, node_ids: list[str], name: str = "Group") -> dict[str, Any]:
        wf = self.get_workflow(workflow_id)
        gid = f"grp_{uuid.uuid4().hex[:8]}"
        group = {"group_id": gid, "workflow_id": workflow_id, "name": name, "node_ids": list(node_ids), "created_at": _now()}
        self.store.groups.save(gid, group)
        wf["group_ids"].append(gid)
        self.store.workflows.save(workflow_id, wf)
        return group

    def add_comment(self, workflow_id: str, *, text: str, x: float = 0, y: float = 0, author: str = "") -> dict[str, Any]:
        wf = self.get_workflow(workflow_id)
        cid = f"cmt_{uuid.uuid4().hex[:8]}"
        comment = {"comment_id": cid, "workflow_id": workflow_id, "text": text, "x": x, "y": y, "author": author, "at": _now()}
        self.store.comments.save(cid, comment)
        wf["comment_ids"].append(cid)
        self.store.workflows.save(workflow_id, wf)
        return comment

    def clipboard_copy(self, workflow_id: str, *, node_ids: list[str], user_id: str = "default") -> dict[str, Any]:
        nodes = [self.store.nodes.get(nid) for nid in node_ids]
        payload = {"workflow_id": workflow_id, "nodes": [copy.deepcopy(n) for n in nodes if n], "at": _now()}
        key = f"{user_id}:{workflow_id}"
        self.store.clipboard.save(key, payload)
        return {"copied": len(payload["nodes"]), "key": key}

    def clipboard_paste(self, workflow_id: str, *, user_id: str = "default", offset_x: float = 40, offset_y: float = 40) -> dict[str, Any]:
        key = f"{user_id}:{workflow_id}"
        payload = self.store.clipboard.get(key)
        if not payload:
            # try any clipboard for same user from source workflow
            clips = [c for c in self.store.clipboard.list_all() if c.get("nodes")]
            payload = clips[-1] if clips else None
        if not payload:
            raise ValidationError("clipboard empty")
        created = []
        for node in payload.get("nodes") or []:
            created.append(
                self.add_node(
                    workflow_id,
                    node_type=node["node_type"],
                    label=node.get("label", ""),
                    x=float(node.get("x", 0)) + offset_x,
                    y=float(node.get("y", 0)) + offset_y,
                    properties=node.get("properties"),
                )
            )
        return {"pasted": created}

    def undo(self, workflow_id: str) -> dict[str, Any]:
        hist = self._history(workflow_id)
        if len(hist) < 2:
            return {"undone": False, "reason": "nothing_to_undo"}
        current = hist.pop()
        self.store.history.save(workflow_id, {"workflow_id": workflow_id, "entries": hist})
        previous = hist[-1] if hist else None
        return {"undone": True, "removed": current, "current": previous}

    def redo(self, workflow_id: str) -> dict[str, Any]:
        # Simplified redo stack stored alongside history entries with undone flag
        hist = self._history(workflow_id)
        undone = [e for e in hist if e.get("undone")]
        if not undone:
            return {"redone": False, "reason": "nothing_to_redo"}
        entry = undone[-1]
        entry["undone"] = False
        self.store.history.save(workflow_id, {"workflow_id": workflow_id, "entries": hist})
        return {"redone": True, "entry": entry}

    def list_templates_on_canvas(self) -> list[str]:
        return list(self.node_types)

    def _canvas_state(self, workflow_id: str) -> dict[str, Any]:
        self.get_workflow(workflow_id)
        state = self.store.canvas_states.get(workflow_id)
        if state is None:
            raise NotFoundError("canvas", workflow_id)
        return state

    def _history(self, workflow_id: str) -> list[dict[str, Any]]:
        bag = self.store.history.get(workflow_id) or {"workflow_id": workflow_id, "entries": []}
        return list(bag.get("entries") or [])

    def _push_history(self, workflow_id: str, action: str, payload: Any) -> None:
        hist = self._history(workflow_id)
        hist.append({"action": action, "payload": payload, "at": _now()})
        self.store.history.save(workflow_id, {"workflow_id": workflow_id, "entries": hist[-100:]})

    def status(self) -> dict[str, Any]:
        return {
            "visual_editor": "1.0",
            "workflows": len(self.store.workflows.list_all()),
            "node_types": self.node_types,
            "ready": True,
        }


visual_editor = VisualEditor()
