# Platform event permission codes — RBAC v2 event registry.

from __future__ import annotations

EVENT_PERMISSIONS: tuple[tuple[str, str], ...] = (
    ("deal.created", "Emit or subscribe to deal created events"),
    ("deal.updated", "Emit or subscribe to deal updated events"),
    ("payment.received", "Emit or subscribe to payment received events"),
    ("partner.assigned", "Emit or subscribe to partner assigned events"),
    ("commission.created", "Emit or subscribe to commission created events"),
    ("ledger.entry.created", "Emit or subscribe to ledger entry created events"),
)

EVENT_PERMISSION_CODES: frozenset[str] = frozenset(code for code, _ in EVENT_PERMISSIONS)
