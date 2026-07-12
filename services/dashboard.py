# Dashboard / analytics aggregations.

class DashboardService:
    SECTIONS = {
        "kpi": "📊 KPI",
        "sales": "📈 Продажи",
        "workload": "📅 Загрузка сотрудников",
        "projects": "📦 Активные проекты",
        "notifications": "🔔 Уведомления",
        "tasks": "📋 Задачи",
    }

    @staticmethod
    def get_kpi(user_id: int) -> dict:
        from database import get_dashboard_kpi
        return get_dashboard_kpi(user_id)

    @staticmethod
    def format_section(user_id: int, section: str) -> str:
        from database import format_dashboard_section
        return format_dashboard_section(user_id, section)

    @staticmethod
    def format_overview(user_id: int) -> str:
        from database import format_dashboard_text
        return format_dashboard_text(user_id)
