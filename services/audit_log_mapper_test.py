# AuditLog mapper smoke test — verifies single ORM registration.

from __future__ import annotations

from pathlib import Path


def run_audit_log_mapper_smoke() -> dict:
    steps: dict = {}
    root = Path(__file__).resolve().parent.parent
    try:
        from database.base import Base
        from database.migration_models import load_all_models
        from database.models.audit_log import AuditAction, AuditLog
        from repositories.audit_repository import AuditRepository

        load_all_models()
        mappers = [m for m in Base.registry.mappers if m.class_.__name__ == "AuditLog"]
        steps["audit_log_mappers"] = len(mappers)
        steps["tablename"] = AuditLog.__tablename__
        steps["audit_repository"] = hasattr(AuditRepository, "create_log")
        steps["audit_actions"] = len(list(AuditAction))

        scheduler_src = (root / "services" / "pg_scheduler_engine.py").read_text(encoding="utf-8")
        steps["scheduler_imports_audit_log"] = (
            "from database.models.audit_log import AuditAction" in scheduler_src
        )
        steps["scheduler_has_worker"] = "get_default_worker" in scheduler_src
        steps["scheduler_has_engine"] = "class SchedulerEngineV1" in scheduler_src

        audit_repo_src = (root / "repositories" / "audit_repository.py").read_text(encoding="utf-8")
        steps["audit_repo_canonical_import"] = (
            "from database.models.audit_log import AuditAction, AuditLog" in audit_repo_src
        )

        ok = (
            steps["audit_log_mappers"] == 1
            and steps["tablename"] == "audit_engine_logs"
            and steps["audit_repository"]
            and steps["scheduler_imports_audit_log"]
            and steps["scheduler_has_worker"]
            and steps["audit_repo_canonical_import"]
        )
        return {"ok": ok, "status": "OK" if ok else "ERROR", "steps": steps}
    except Exception as exc:
        return {"ok": False, "status": "ERROR", "steps": steps, "error": str(exc)}


def run_audit_log_mapper_smoke_test() -> dict:
    return run_audit_log_mapper_smoke()
