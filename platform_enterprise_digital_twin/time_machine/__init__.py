"""Time Machine — Sprint 24.5."""

from __future__ import annotations

from typing import Any

from platform_enterprise_digital_twin.models import TIME_PRESETS


class TimeMachine:
    def __init__(self) -> None:
        self._snapshots: dict[str, list[dict[str, Any]]] = {}

    def save_snapshot(self, *, company_id: str, label: str, state: dict[str, Any]) -> dict[str, Any]:
        item = {"label": label, "state": dict(state)}
        self._snapshots.setdefault(company_id, []).append(item)
        return dict(item)

    def recall(self, *, company_id: str, preset: str = "1h", custom_label: str = "") -> dict[str, Any]:
        preset = (preset or "1h").lower()
        if preset not in TIME_PRESETS:
            raise ValueError(f"unsupported preset: {preset}")
        snaps = list(self._snapshots.get(company_id) or [])
        if preset == "custom":
            match = next((s for s in reversed(snaps) if s.get("label") == custom_label), None)
        else:
            match = next((s for s in reversed(snaps) if s.get("label") == preset), snaps[-1] if snaps else None)
        return {
            "company_id": company_id,
            "preset": preset,
            "found": match is not None,
            "snapshot": match,
            "available_presets": list(TIME_PRESETS),
        }

    def compare(self, *, a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
        ma = (a.get("state") or a).get("metrics") or (a.get("state") or {})
        mb = (b.get("state") or b).get("metrics") or (b.get("state") or {})
        keys = set(ma) | set(mb)
        diffs = {k: {"a": ma.get(k), "b": mb.get(k)} for k in keys if ma.get(k) != mb.get(k)}
        return {"diffs": diffs, "changed_keys": list(diffs.keys()), "comparable": True}
