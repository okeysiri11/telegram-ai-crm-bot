# Audit Center facade — Sprint 32.4.

from __future__ import annotations

from typing import Any

from platform_security.audit import AuditTrail


class AuditCenter:
    def __init__(self, trail: AuditTrail | None = None) -> None:
        self._trail = trail or AuditTrail()

    def record(self, *, action: str, actor: str, resource: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
        entry = self._trail.record(action=action, actor=actor, resource=resource, details=meta)
        return entry

    def summary(self) -> dict[str, Any]:
        st = self._trail.status()
        return {
            "entries": st.get("entries", 0),
            "sealed": st.get("sealed", False),
            "export_formats": ["json", "csv"],
            "compliance": ["gdpr", "iso27001", "soc2"],
        }

    def export_report(self) -> dict[str, Any]:
        return {
            "report": "security_audit",
            "generated": True,
            "frameworks": ["GDPR", "ISO27001", "SOC2"],
            "summary": self.summary(),
            "entries": self._trail.list_all()[-100:],
        }

    def capabilities(self) -> dict[str, Any]:
        return {
            "audit_trail": True,
            "security_reports": True,
            "audit_export": True,
            "gdpr": True,
            "iso27001": True,
            "soc2": True,
        }
