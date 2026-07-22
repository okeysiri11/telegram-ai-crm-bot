# Diagnostics — OBD, inspection, photos, damage, AI bridge.

from __future__ import annotations

from applications.auto_marketplace.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.auto_marketplace.service_centers.models import DiagnosticReport
from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class DiagnosticsEngine:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        platform: PlatformBridge | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._platform = platform or platform_bridge

    def create_report(self, report: DiagnosticReport) -> DiagnosticReport:
        if not report.vehicle_id and not report.vin:
            raise ValidationError("vehicle_id or vin is required")
        if report.obd_codes and not report.recommendations:
            report.recommendations = [f"Investigate code {c}" for c in report.obd_codes[:5]]
        if report.damage and "Body repair assessment" not in report.recommendations:
            report.recommendations.append("Body repair assessment")
        return self._store.diagnostic_reports.save(report.report_id, report)

    async def ai_analyze(self, report_id: str) -> DiagnosticReport:
        report = self._store.diagnostic_reports.get(report_id)
        if report is None:
            from applications.auto_marketplace.shared.exceptions import NotFoundError

            raise NotFoundError("DiagnosticReport", report_id)
        codes = ", ".join(report.obd_codes) or "none"
        report.ai_summary = f"AI diagnostics: OBD[{codes}]; damage={len(report.damage)}; photos={len(report.photos)}"
        if not report.recommendations:
            report.recommendations = ["Schedule inspection with service advisor"]
        await self._platform.store_customer_context(
            f"diagnostics:{report_id}",
            {"ai_summary": report.ai_summary, "vehicle_id": report.vehicle_id},
        )
        return self._store.diagnostic_reports.save(report_id, report)

    def list_for_vehicle(self, vehicle_id: str) -> list[DiagnosticReport]:
        return [r for r in self._store.diagnostic_reports.list_all() if r.vehicle_id == vehicle_id]

    def metrics(self) -> dict:
        return {"diagnostic_reports": self._store.diagnostic_reports.count()}


diagnostics_engine = DiagnosticsEngine()
