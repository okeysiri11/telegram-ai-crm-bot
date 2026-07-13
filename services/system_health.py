# System Health Dashboard — component status overview.

from services.platform_test import PlatformTestService
from services.production_readiness_suite import ProductionReadinessSuite


class SystemHealthService:
    @staticmethod
    def check_component(name: str) -> str:
        ok, detail = PlatformTestService.run_component_check(name)
        if ok:
            return "ONLINE"
        if detail and "missing" not in detail.lower():
            return "DEGRADED"
        return "OFFLINE"

    @staticmethod
    async def get_production_snapshot() -> dict:
        diagnostics = await ProductionReadinessSuite.run_diagnostics()
        checks = diagnostics.get("checks") or {}
        mapping = {
            "Startup": "startup",
            "Database": "database",
            "Redis": "redis",
            "API": "api",
            "Scheduler": "scheduler",
            "Telegram": "telegram",
        }
        snapshot = {}
        status_map = {
            "healthy": "ONLINE",
            "degraded": "DEGRADED",
            "unhealthy": "OFFLINE",
            "skipped": "SKIPPED",
        }
        for label, key in mapping.items():
            item = checks.get(key, {})
            snapshot[label] = status_map.get(item.get("status"), "OFFLINE")
        snapshot["readiness"] = diagnostics.get("status", "unknown")
        snapshot["ready"] = diagnostics.get("ready", False)
        snapshot["alerts"] = await ProductionReadinessSuite.get_active_alerts()
        return snapshot

    @staticmethod
    def get_health_snapshot() -> dict:
        components = {
            "Database": "DATABASE",
            "Telegram": "TELEGRAM",
            "AI Router": "AI_ROUTER",
            "Workflow": "WORKFLOW",
            "Calendar": "CALENDAR",
            "Notifications": "NOTIFY",
            "Search": "SEARCH",
            "Files": "FILES",
            "Audit": "AUDIT",
            "Automotive UI": "AUTOMOTIVE_UI",
        }
        snapshot = {}
        for label, key in components.items():
            snapshot[label] = SystemHealthService.check_component(key)
        from database import get_last_platform_health
        snapshot["last_test"] = get_last_platform_health()
        snapshot["PostgreSQL"] = SystemHealthService._postgres_status()
        return snapshot

    @staticmethod
    def _postgres_status() -> str:
        from database.connection import is_postgres_configured
        return "ONLINE" if is_postgres_configured() else "OFFLINE"

    @staticmethod
    async def format_health_dashboard_async() -> str:
        prod = await SystemHealthService.get_production_snapshot()
        icons = {"ONLINE": "🟢", "DEGRADED": "🟡", "OFFLINE": "🔴", "SKIPPED": "⚪"}
        lines = [
            "❤️ System Health",
            "",
            f"Production readiness: {prod.get('readiness', '—').upper()}",
            f"Ready for traffic: {'yes' if prod.get('ready') else 'no'}",
            "",
            "Dependencies:",
        ]
        for label in ("Startup", "Database", "Redis", "API", "Scheduler", "Telegram"):
            status = prod.get(label, "OFFLINE")
            lines.append(f"{icons.get(status, '⚪')} {label}: {status}")
        alerts = prod.get("alerts") or []
        if alerts:
            lines.append(f"\nActive alerts: {len(alerts)}")
            for alert in alerts[:5]:
                lines.append(f"• [{alert['severity']}] {alert['component']}: {alert['message']}")
        legacy = SystemHealthService.get_health_snapshot()
        last = legacy.get("last_test") or {}
        tested_at = last.get("tested_at", "—")
        platform_status = last.get("status", "—")
        scores = last.get("scores") or {}
        lines.append(f"\nПоследний platform test:\n{tested_at}")
        lines.append(f"Platform: {platform_status}")
        if scores:
            lines.append(
                f"Readiness: {scores.get('platform', '—')}% | "
                f"Commercial: {scores.get('commercial', '—')}% | "
                f"Debt: {scores.get('technical_debt', '—')}%"
            )
        return "\n".join(lines)

    @staticmethod
    def format_health_dashboard() -> str:
        snap = SystemHealthService.get_health_snapshot()
        icons = {"ONLINE": "🟢", "DEGRADED": "🟡", "OFFLINE": "🔴"}
        lines = ["❤️ System Health\n"]
        for label in (
            "Database", "PostgreSQL", "Telegram", "AI Router", "Workflow",
            "Calendar", "Notifications", "Search", "Files", "Audit",
            "Automotive UI",
        ):
            status = snap.get(label, "OFFLINE")
            lines.append(f"{icons.get(status, '⚪')} {label}: {status}")
        last = snap.get("last_test") or {}
        tested_at = last.get("tested_at", "—")
        platform_status = last.get("status", "—")
        scores = last.get("scores") or {}
        lines.append(f"\nПоследний тест:\n{tested_at}")
        lines.append(f"Platform: {platform_status}")
        if scores:
            lines.append(
                f"Readiness: {scores.get('platform', '—')}% | "
                f"Commercial: {scores.get('commercial', '—')}% | "
                f"Debt: {scores.get('technical_debt', '—')}%"
            )
        lines.append("\nRun ❤️ System Health for production dependency checks.")
        return "\n".join(lines)
