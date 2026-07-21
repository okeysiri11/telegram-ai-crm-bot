# Executive decision support — briefs and strategic reports.

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.analytics.ai_integration import AnalyticsAIIntegration, analytics_ai
from applications.agro_marketplace.analytics.models import BIReport
from applications.agro_marketplace.kpi.service import KPIService, kpi_service
from applications.agro_marketplace.reporting.service import ReportingService, reporting_service


class ExecutiveService:
    def __init__(
        self,
        kpi: KPIService | None = None,
        reporting: ReportingService | None = None,
        ai: AnalyticsAIIntegration | None = None,
    ) -> None:
        self._kpi = kpi or kpi_service
        self._reporting = reporting or reporting_service
        self._ai = ai or analytics_ai

    async def build_executive_report(self, *, title: str = "Executive Agro Brief") -> BIReport:
        snapshots = await self._kpi.calculate_all()
        metrics = {s.name.value: s.value for s in snapshots}
        brief = await self._ai.executive_report("agro marketplace performance", metrics)
        recommendations = await self._ai.optimize_recommendations("executive", metrics)
        risks = await self._ai.predict_risks("enterprise", {
            "warehouse_utilization": metrics.get("warehouse_utilization", 0),
            "export_at_risk": 1 if metrics.get("export_volume", 0) == 0 else 0,
        })
        report = BIReport(
            title=title,
            report_type="executive",
            summary=str(brief.get("summary") or brief.get("brief") or "Executive performance overview"),
            sections=[
                {"name": "kpi_summary", "metrics": metrics},
                {"name": "ai_brief", "content": brief},
                {"name": "risk", "content": risks},
            ],
            kpis=[s.to_dict() for s in snapshots],
            recommendations=recommendations,
        )
        return await self._reporting.publish_executive(report)

    async def decision_pack(self) -> dict[str, Any]:
        report = await self.build_executive_report()
        return {
            "report": report.to_dict(),
            "kpis": self._kpi.latest_map(),
        }


executive_service = ExecutiveService()
