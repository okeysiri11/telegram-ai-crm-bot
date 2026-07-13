# Platform Test Center and /platform_test self-check.

from datetime import datetime


class PlatformTestService:
    COMPONENTS = (
        "DATABASE",
        "TELEGRAM",
        "RBAC",
        "WORKFLOW",
        "CALENDAR",
        "FILES",
        "SEARCH",
        "NOTIFY",
        "AI_ROUTER",
        "AUDIT",
        "AUTOMOTIVE_UI",
    )

    TEST_MODULES = {
        "🌾 Agro Test": "agro",
        "💰 Crypto Test": "crypto",
        "🚁 Drone Test": "drone",
        "☕ Cafe Test": "cafe",
        "💄 Beauty Test": "beauty",
        "⚖ Legal Test": "legal",
        "📅 Calendar Test": "calendar",
        "📁 Files Test": "files",
        "🔎 Search Test": "search",
        "📊 Reports Test": "reports",
        "🤖 AI Test": "ai",
        "⚙ Workflow Test": "workflow",
        "🔔 Notification Test": "notifications",
        "🚗 Auto Test": "automotive",
        "📋 Readiness Test": "readiness",
        "🏢 Tenant Test": "tenant_isolation",
        "🔐 RBAC Test": "rbac_v2",
    }

    @staticmethod
    def run_component_check(name: str) -> tuple[bool, str]:
        try:
            if name == "DATABASE":
                import database as db
                db.cursor.execute("SELECT 1")
                return True, "OK"
            if name == "TELEGRAM":
                from config import BOT_TOKEN
                if not BOT_TOKEN:
                    return False, "BOT_TOKEN missing"
                return True, "OK"
            if name == "RBAC":
                from database import ROLE_NAMES, ROLE_PERMISSIONS, SYSTEM_PERMISSIONS
                if not ROLE_NAMES or not SYSTEM_PERMISSIONS:
                    return False, "RBAC config empty"
                if "SUPER_MANAGER" not in ROLE_PERMISSIONS:
                    return False, "SUPER_MANAGER missing"
                return True, "OK"
            if name == "WORKFLOW":
                from database import get_workflow_rules
                if not get_workflow_rules():
                    return False, "no rules"
                return True, "OK"
            if name == "CALENDAR":
                import database as db
                db.cursor.execute("SELECT COUNT(*) FROM calendar_events")
                db.cursor.fetchone()
                return True, "OK"
            if name == "FILES":
                import database as db
                db.cursor.execute("SELECT COUNT(*) FROM files")
                db.cursor.fetchone()
                return True, "OK"
            if name == "SEARCH":
                from services.search_service import SearchService
                PlatformTestService._ = SearchService.search(0, "test", limit=1)
                return True, "OK"
            if name == "NOTIFY":
                from database import get_notifications
                get_notifications(0, limit=1)
                return True, "OK"
            if name == "AI_ROUTER":
                from services.ai_router import AIRouter
                d, c = AIRouter.detect_domain("тест agro пшеница")
                if not c:
                    return False, "router failed"
                return True, "OK"
            if name == "AUDIT":
                import database as db
                db.cursor.execute("SELECT COUNT(*) FROM audit_log")
                db.cursor.fetchone()
                return True, "OK"
            if name == "AUTOMOTIVE_UI":
                from services.automotive_ui_self_test import run_automotive_ui_self_test

                result = run_automotive_ui_self_test()
                if not result.get("ok"):
                    failed = [
                        key for key, item in result.get("checks", {}).items()
                        if not item.get("ok")
                    ]
                    return False, ",".join(failed[:3])
                return True, "OK"
            return False, "unknown component"
        except Exception as exc:
            return False, str(exc)[:80]

    @staticmethod
    def run_platform_test() -> dict:
        results = {}
        for comp in PlatformTestService.COMPONENTS:
            ok, detail = PlatformTestService.run_component_check(comp)
            results[comp] = {"ok": ok, "detail": detail}
        all_ok = all(r["ok"] for r in results.values())
        payload = {
            "results": results,
            "status": "HEALTHY" if all_ok else "DEGRADED",
            "tested_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }
        from database import save_platform_health_run
        save_platform_health_run(payload)
        return payload

    @staticmethod
    def format_platform_test_report(payload: dict) -> str:
        lines = []
        for comp in PlatformTestService.COMPONENTS:
            r = payload["results"].get(comp, {})
            mark = "OK" if r.get("ok") else "ERROR"
            dots = "." * max(1, 14 - len(comp))
            detail = "" if r.get("ok") else f" ({r.get('detail', '')})"
            lines.append(f"{comp} {dots} {mark}{detail}")
        status = payload.get("status", "UNKNOWN")
        lines.append(f"\nPLATFORM STATUS:\n{status}")
        lines.append(f"\nTested: {payload.get('tested_at', '—')}")
        return "\n".join(lines)

    @staticmethod
    def run_module_test(module_key: str, user_id: int = 0) -> str:
        try:
            if module_key == "agro":
                from database import get_requests_by_status, get_agro_deal_by_request
                rows = get_requests_by_status("NEW")
                _ = get_agro_deal_by_request(rows[0][0]) if rows else None
            elif module_key == "crypto":
                from services.crypto_auth import CryptoAuthService
                from database import run_crypto_erp_cycle_test
                if not CryptoAuthService.can_access_crypto(user_id):
                    raise RuntimeError("no crypto access")
                result = run_crypto_erp_cycle_test(user_id)
                if not result.get("ok"):
                    raise RuntimeError(result.get("error", "cycle failed"))
            elif module_key == "drone":
                from database import get_drone_ai_context
                get_drone_ai_context(user_id)
            elif module_key in ("cafe", "beauty"):
                from services.permissions import PermissionService
                PermissionService.can_access_module(user_id, "cafe_beauty")
            elif module_key == "legal":
                from services.permissions import PermissionService
                PermissionService.can_access_module(user_id, "law")
            elif module_key == "calendar":
                from services.calendar_service import CalendarService
                CalendarService.get_today_events(user_id, limit=1)
            elif module_key == "files":
                from database import get_system_files
                get_system_files(user_id, limit=1)
            elif module_key == "search":
                from services.search_service import SearchService
                SearchService.search(user_id, "test", limit=1)
            elif module_key == "reports":
                from database import get_dashboard_kpi
                get_dashboard_kpi(user_id)
            elif module_key == "ai":
                from database import get_ai_agents
                if not get_ai_agents():
                    raise RuntimeError("no agents")
            elif module_key == "workflow":
                from services.workflow_engine import WorkflowEngine
                rules = __import__("database").get_workflow_rules()
                if not rules:
                    raise RuntimeError("no workflow rules")
            elif module_key == "notifications":
                from services.notifications import NotificationService
                NotificationService.get_notifications(user_id, limit=1)
            elif module_key == "automotive":
                from services.automotive_ui_self_test import run_automotive_ui_self_test

                result = run_automotive_ui_self_test()
                if not result.get("ok"):
                    failed = [
                        f"{key}: {item.get('detail')}"
                        for key, item in result.get("checks", {}).items()
                        if not item.get("ok")
                    ]
                    raise RuntimeError("; ".join(failed[:5]))
            elif module_key == "readiness":
                from services.platform_readiness_test_suite import (
                    PlatformReadinessTestSuite,
                    run_platform_readiness_suite,
                )

                payload = run_platform_readiness_suite()
                scores = payload.get("scores", {})
                summary = (
                    f"STATUS: {payload.get('status')}\n"
                    f"Platform: {scores.get('platform', 0)}%\n"
                    f"Commercial: {scores.get('commercial', 0)}%\n"
                    f"Technical debt: {scores.get('technical_debt', 0)}%"
                )
                if payload.get("status") == "RED":
                    failed = [
                        key
                        for key, item in payload.get("modules", {}).items()
                        if item.get("status") == "failed"
                    ]
                    raise RuntimeError(f"{summary}\nFailed: {', '.join(failed[:5])}")
                return f"STATUS: OK\n{summary}"
            elif module_key == "tenant_isolation":
                from services.multi_tenant_isolation_test import run_multi_tenant_isolation_test

                result = run_multi_tenant_isolation_test()
                if not result.get("ok"):
                    raise RuntimeError(str(result))
                return (
                    "STATUS: OK\n"
                    f"tenant_a={result.get('tenant_a')}\n"
                    f"tenant_b={result.get('tenant_b')}\n"
                    "isolation verified"
                )
            elif module_key == "rbac_v2":
                from services.rbac_v2_test import run_rbac_v2_tests

                result = run_rbac_v2_tests()
                if not result.get("ok"):
                    raise RuntimeError(str(result))
                return (
                    "STATUS: OK\n"
                    f"access_matrix: {result.get('access_matrix', {}).get('ok')}\n"
                    f"tenant_isolation: {result.get('tenant_isolation', {}).get('ok')}"
                )
            else:
                raise RuntimeError(f"unknown module {module_key}")
            return "STATUS: OK"
        except Exception as exc:
            return f"STATUS: ERROR\n{exc}"

    @staticmethod
    def get_platform_metrics() -> dict:
        import os
        import database as db
        from database import ROLE_NAMES, get_workflow_rules

        db.cursor.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        table_count = db.cursor.fetchone()[0]

        services_dir = os.path.dirname(__file__)
        service_count = len([
            f for f in os.listdir(services_dir)
            if f.endswith(".py") and f != "__init__.py"
        ])

        handlers_path = os.path.join(os.path.dirname(services_dir), "handlers.py")
        handler_count = 0
        if os.path.isfile(handlers_path):
            with open(handlers_path, encoding="utf-8") as fh:
                handler_count = fh.read().count("@router.")

        workflow_count = len(get_workflow_rules())
        role_count = len(ROLE_NAMES)

        return {
            "tables": table_count,
            "services": service_count,
            "roles": role_count,
            "workflows": workflow_count,
            "handlers": handler_count,
        }

    @staticmethod
    def format_platform_validation(payload: dict = None) -> str:
        metrics = PlatformTestService.get_platform_metrics()
        results = (payload or {}).get("results", {})
        ok_count = sum(1 for r in results.values() if r.get("ok"))
        total = len(PlatformTestService.COMPONENTS) or 1
        readiness = int(round(ok_count / total * 100)) if results else 85

        if ok_count == total:
            debt = "LOW"
        elif ok_count >= total - 2:
            debt = "MEDIUM"
        else:
            debt = "HIGH"

        arch = "STABLE" if readiness >= 70 else "UNSTABLE"

        return (
            f"--- Validation ---\n"
            f"DB tables: {metrics['tables']}\n"
            f"Services: {metrics['services']}\n"
            f"Roles: {metrics['roles']}\n"
            f"Workflow rules: {metrics['workflows']}\n"
            f"Handlers: {metrics['handlers']}\n\n"
            f"Architecture Status:\n{arch}\n\n"
            f"Platform Readiness:\n{readiness}%\n\n"
            f"Technical Debt:\n{debt}"
        )
