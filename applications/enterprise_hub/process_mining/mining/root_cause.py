from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"



from applications.enterprise_hub.process_mining.models import ROOT_CAUSES


class RootCauseMining:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def analyze(self, *, process_id: str, conformance_id: str | None = None) -> dict[str, Any]:
        causes = []
        conf = self.store.epm_conformance.get(conformance_id) if conformance_id else None
        viol = (conf or {}).get("violations") or []
        if any(v.get("kind") == "sla_breach" for v in viol):
            causes.append({"cause": "department_overload", "confidence": 0.78})
            causes.append({"cause": "staff_shortage", "confidence": 0.66})
        if any(v.get("kind") == "skipped_step" for v in viol):
            causes.append({"cause": "human_factor", "confidence": 0.71})
        if any(v.get("kind") == "extra_step" for v in viol):
            causes.append({"cause": "integration_error", "confidence": 0.55})
        if not causes:
            causes = [
                {"cause": "supplier_delay", "confidence": 0.5},
                {"cause": "missing_materials", "confidence": 0.45},
            ]
        for c in causes:
            if c["cause"] not in ROOT_CAUSES:
                raise ValidationError(f"invalid cause: {c['cause']}")
        rid = _id("epm_rc")
        return self.store.epm_root_causes.save(
            rid,
            {
                "analysis_id": rid,
                "process_id": process_id,
                "conformance_id": conformance_id,
                "causes": causes,
                "top_cause": causes[0]["cause"],
                "at": _now(),
            },
        )
