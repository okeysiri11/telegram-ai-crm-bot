#!/usr/bin/env python3
"""Smoke test for single AuditLog ORM mapper registration."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from database.base import Base
    from database.migration_models import load_all_models
    from database.models.audit_log import AuditLog
    from repositories.audit_repository import AuditRepository

    load_all_models()
    mappers = [m for m in Base.registry.mappers if m.class_.__name__ == "AuditLog"]
    print(f"AuditLog mappers: {len(mappers)}")
    print(f"AuditLog tablename: {AuditLog.__tablename__}")
    assert len(mappers) == 1, "duplicate AuditLog mapper registration"
    assert AuditLog.__tablename__ == "audit_engine_logs"
    assert hasattr(AuditRepository, "create_log")

    scheduler_src = (ROOT / "services" / "pg_scheduler_engine.py").read_text(encoding="utf-8")
    assert "from database.models.audit_log import AuditAction" in scheduler_src

    tables = sorted(Base.metadata.tables.keys())
    required = {
        "users", "roles", "user_roles", "permissions", "role_permissions",
        "deals", "platform_events", "ledger_entries",
        "commission_rules", "commissions", "commission_payments",
        "partners", "partner_deal_assignments", "calendar_events",
        "tasks", "notifications", "ai_agents", "audit_engine_logs",
    }
    missing = sorted(required - set(tables))
    print(f"tables: {len(tables)}, missing required: {missing}")
    assert not missing

    print("ALL SMOKE TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
