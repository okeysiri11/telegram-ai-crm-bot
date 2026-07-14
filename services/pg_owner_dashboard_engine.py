# Owner Dashboard v1 — unified metrics across Lead, Deal, Revenue engines.

from __future__ import annotations

from decimal import Decimal
from typing import Any

from database.session import get_session
from repositories.owner_dashboard_repository import OwnerDashboardRepository


class OwnerDashboardEngineV1:
    @staticmethod
    async def get_dashboard() -> dict[str, Any]:
        today = OwnerDashboardRepository.start_of_today()
        month = OwnerDashboardRepository.start_of_month()

        async with get_session() as session:
            repo = OwnerDashboardRepository(session)

            auto = {
                "leads": await repo.count_leads(vertical="auto"),
                "leads_month": await repo.count_leads(vertical="auto", since=month),
                "deals": await repo.count_deals(vertical="auto"),
                "deals_completed": await repo.count_deals(
                    vertical="auto",
                    status="COMPLETED",
                ),
                "revenue": await repo.sum_revenue_platform(vertical="auto"),
                "revenue_month": await repo.sum_revenue_platform(vertical="auto", since=month),
            }
            agro = {
                "leads": await repo.count_leads(vertical="agro"),
                "leads_month": await repo.count_leads(vertical="agro", since=month),
                "deals": await repo.count_deals(vertical="agro"),
                "deals_completed": await repo.count_deals(
                    vertical="agro",
                    status="COMPLETED",
                ),
                "revenue": await repo.sum_revenue_platform(vertical="agro"),
                "revenue_month": await repo.sum_revenue_platform(vertical="agro", since=month),
            }

            global_metrics = {
                "total_income": await repo.sum_revenue_platform(),
                "total_income_month": await repo.sum_revenue_platform(since=month),
                "total_income_today": await repo.sum_revenue_platform(since=today),
                "commissions": await repo.sum_commissions(),
                "commissions_month": await repo.sum_commissions(since=month),
                "top_partners": await repo.top_partners(since=month),
                "top_managers": await repo.top_managers(since=month),
            }

            marketing = {
                "leads_today": await repo.count_leads(since=today),
                "leads_month": await repo.count_leads(since=month),
                "by_source": await repo.leads_by_source(since=month),
                "by_utm": await repo.leads_by_utm(since=month),
            }

            revenue_detail = await repo.revenue_breakdown(since=month)

        return {
            "auto": auto,
            "agro": agro,
            "global": global_metrics,
            "marketing": marketing,
            "revenue_detail": revenue_detail,
        }

    @staticmethod
    def format_main_dashboard(data: dict[str, Any]) -> str:
        auto = data["auto"]
        agro = data["agro"]
        g = data["global"]
        lines = [
            "📊 Owner Dashboard v1",
            "",
            "🚗 AUTO",
            f"  Leads: {auto['leads']} (month: {auto['leads_month']})",
            f"  Deals: {auto['deals']} (completed: {auto['deals_completed']})",
            f"  Revenue: {auto['revenue']} (month: {auto['revenue_month']})",
            "",
            "🌾 AGRO",
            f"  Leads: {agro['leads']} (month: {agro['leads_month']})",
            f"  Deals: {agro['deals']} (completed: {agro['deals_completed']})",
            f"  Revenue: {agro['revenue']} (month: {agro['revenue_month']})",
            "",
            "🌍 Global",
            f"  Total income: {g['total_income']} (month: {g['total_income_month']}, today: {g['total_income_today']})",
            f"  Commissions: {g['commissions']} (month: {g['commissions_month']})",
            "",
            "🤝 Top partners (month):",
        ]
        lines.extend(OwnerDashboardEngineV1._format_ranking(g.get("top_partners"), income_key=1))
        lines.append("")
        lines.append("👥 Top managers (month):")
        lines.extend(OwnerDashboardEngineV1._format_ranking(g.get("top_managers"), income_key=1))
        return "\n".join(lines)

    @staticmethod
    def format_marketing_analytics(data: dict[str, Any]) -> str:
        m = data["marketing"]
        lines = [
            "📈 Marketing Analytics",
            "",
            f"Leads today: {m['leads_today']}",
            f"Leads this month: {m['leads_month']}",
            "",
            "By source link:",
        ]
        for source, count in m.get("by_source") or []:
            lines.append(f"  • {source or '—'}: {count}")
        if not m.get("by_source"):
            lines.append("  • —")
        lines.append("")
        lines.append("By UTM source:")
        for utm, count in m.get("by_utm") or []:
            lines.append(f"  • {utm or '—'}: {count}")
        if not m.get("by_utm"):
            lines.append("  • —")
        return "\n".join(lines)

    @staticmethod
    def format_revenue_analytics(data: dict[str, Any]) -> str:
        r = data["revenue_detail"]
        g = data["global"]
        auto = data["auto"]
        agro = data["agro"]
        lines = [
            "💰 Revenue Analytics",
            "",
            f"Gross (month): {r['gross']}",
            f"Platform income (month): {r['platform']}",
            f"Partner share (month): {r['partner']}",
            f"Manager share (month): {r['manager']}",
            f"Referral share (month): {r['referral']}",
            "",
            f"Total commissions (month): {g['commissions_month']}",
            "",
            "By vertical (month):",
            f"  • AUTO: {auto['revenue_month']}",
            f"  • AGRO: {agro['revenue_month']}",
        ]
        return "\n".join(lines)

    @staticmethod
    def format_manager_analytics(data: dict[str, Any]) -> str:
        g = data["global"]
        lines = [
            "👥 Manager Analytics",
            "",
            "Top managers by commission (month):",
        ]
        for entry in g.get("top_managers") or []:
            manager_id, income, deals = entry
            label = "unassigned" if manager_id == "unassigned" else f"{manager_id[:8]}…"
            lines.append(f"  • {label}: {income} ({deals} deals)")
        if not g.get("top_managers"):
            lines.append("  • —")
        return "\n".join(lines)

    @staticmethod
    def format_partner_analytics(data: dict[str, Any]) -> str:
        g = data["global"]
        lines = [
            "🤝 Partner Analytics",
            "",
            "Top partners by commission (month):",
        ]
        for entry in g.get("top_partners") or []:
            partner_id, income, deals = entry
            label = "direct" if partner_id == "direct" else f"{partner_id[:8]}…"
            lines.append(f"  • {label}: {income} ({deals} deals)")
        if not g.get("top_partners"):
            lines.append("  • —")
        return "\n".join(lines)

    @staticmethod
    def _format_ranking(
        entries: list[tuple] | None,
        *,
        income_key: int,
    ) -> list[str]:
        if not entries:
            return ["  • —"]
        lines = []
        for entry in entries[:5]:
            entity_id = entry[0]
            income = entry[income_key]
            label = entity_id if entity_id in {"direct", "unassigned"} else f"{str(entity_id)[:8]}…"
            lines.append(f"  • {label}: {income}")
        return lines
