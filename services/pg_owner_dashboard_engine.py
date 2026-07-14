# Owner Dashboard v1 — unified metrics across Lead, Deal, Revenue engines.

from __future__ import annotations

from decimal import Decimal
from typing import Any

from database.session import get_session
from repositories.owner_dashboard_repository import OwnerDashboardRepository
from services.pg_crm_pipeline_boards_engine import CrmPipelineBoardsEngineV1
from services.pg_sla_tracking_v1 import SlaTrackingV1
from services.pg_anti_loss_layer_v1 import AntiLossLayerV1
from services.pg_marketing_analytics_v1 import MarketingAnalyticsV1


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

        pipeline = await CrmPipelineBoardsEngineV1.get_pipeline_metrics()
        sla = await SlaTrackingV1.get_owner_metrics()
        anti_loss = await AntiLossLayerV1.get_owner_metrics()
        marketing_v1 = await MarketingAnalyticsV1.get_owner_metrics()

        return {
            "auto": auto,
            "agro": agro,
            "global": global_metrics,
            "marketing": marketing,
            "marketing_v1": marketing_v1,
            "revenue_detail": revenue_detail,
            "pipeline": pipeline,
            "sla": sla,
            "anti_loss": anti_loss,
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
        sla = data.get("sla") or {}
        avg_resp = sla.get("avg_response_minutes")
        if avg_resp is not None:
            from services.pg_sla_tracking_v1 import SlaTrackingV1

            lines.append("")
            lines.append("⏱ SLA snapshot:")
            lines.append(
                f"  Avg response: {avg_resp} min "
                f"{SlaTrackingV1.traffic_light_emoji(int(avg_resp))}"
            )
            lines.append(f"  Overdue leads: {sla.get('overdue_leads', 0)}")
            lines.append(f"  Violations: {sla.get('sla_violations', 0)}")
        anti = data.get("anti_loss") or {}
        lines.append("")
        lines.append("🛡 Anti Loss snapshot:")
        lines.append(f"  Leads prevented: {anti.get('duplicate_leads_prevented', 0)}")
        lines.append(f"  Deals prevented: {anti.get('duplicate_deals_prevented', 0)}")
        mkt = data.get("marketing_v1") or {}
        best = mkt.get("best_source")
        if best:
            lines.append("")
            lines.append("📈 Marketing snapshot:")
            lines.append(
                f"  Best source: {best['source']} (ROI {best['roi']}%)"
            )
        return "\n".join(lines)

    @staticmethod
    def format_marketing_analytics(data: dict[str, Any]) -> str:
        return MarketingAnalyticsV1.format_owner_marketing_analytics(data)

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
    def format_pipeline_analytics(data: dict[str, Any]) -> str:
        return CrmPipelineBoardsEngineV1.format_pipeline_analytics(
            data.get("pipeline") or {}
        )

    @staticmethod
    def format_sla_analytics(data: dict[str, Any]) -> str:
        return SlaTrackingV1.format_owner_sla_analytics(data)

    @staticmethod
    def format_anti_loss_analytics(data: dict[str, Any]) -> str:
        return AntiLossLayerV1.format_owner_anti_loss_analytics(data)

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
