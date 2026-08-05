"""Security audit package — AuditManager (layer) + AuditTrail (immutable hash chain)."""

from __future__ import annotations

from platform_security.audit.manager import AuditManager, audit_manager
from platform_security.audit.trail import AuditTrail

__all__ = [
    "AuditManager",
    "audit_manager",
    "AuditTrail",
]
