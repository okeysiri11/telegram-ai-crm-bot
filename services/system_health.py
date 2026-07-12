# System Health Dashboard — component status overview.

from services.platform_test import PlatformTestService


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
        }
        snapshot = {}
        for label, key in components.items():
            snapshot[label] = SystemHealthService.check_component(key)
        from database import get_last_platform_health
        snapshot["last_test"] = get_last_platform_health()
        return snapshot

    @staticmethod
    def format_health_dashboard() -> str:
        snap = SystemHealthService.get_health_snapshot()
        icons = {"ONLINE": "🟢", "DEGRADED": "🟡", "OFFLINE": "🔴"}
        lines = ["❤️ System Health\n"]
        for label in (
            "Database", "Telegram", "AI Router", "Workflow",
            "Calendar", "Notifications", "Search", "Files", "Audit",
        ):
            status = snap.get(label, "OFFLINE")
            lines.append(f"{icons.get(status, '⚪')} {label}: {status}")
        last = snap.get("last_test") or {}
        tested_at = last.get("tested_at", "—")
        platform_status = last.get("status", "—")
        lines.append(f"\nПоследний тест:\n{tested_at}")
        lines.append(f"Platform: {platform_status}")
        return "\n".join(lines)
