# Production readiness and release certification.

from __future__ import annotations

from events.publisher import publish

from applications.agro_marketplace.config import DEFAULT_CONFIG, AgroMarketplaceConfig
from applications.agro_marketplace.ops.events import (
    CertificationCompletedEvent,
    DeploymentVerifiedEvent,
    ProductionReadyEvent,
    ReleaseCreatedEvent,
)
from applications.agro_marketplace.ops.models import ReadinessSnapshot, ReleaseRecord, ReportKind
from applications.agro_marketplace.ops.qa import QAService, qa_service
from applications.agro_marketplace.ops.validation import ValidationService, validation_service
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class OpsEngine:
    def __init__(
        self,
        store: AgroStore | None = None,
        config: AgroMarketplaceConfig | None = None,
        validation: ValidationService | None = None,
        qa: QAService | None = None,
    ) -> None:
        self._store = store or agro_store
        self._config = config or DEFAULT_CONFIG
        self.validation = validation or validation_service
        self.qa = qa or qa_service

    def version_info(self) -> dict:
        return {
            "application": "agro_marketplace",
            "application_name": self._config.application_name,
            "application_version": self._config.application_version,
            "application_status": self._config.application_status,
            "release": self._config.release,
            "platform_dependency": self._config.platform_dependency,
            "ecosystem_dependency": self._config.ecosystem_dependency,
            "engines": {
                "agro_ai": self._config.agro_ai,
                "export_engine": self._config.export_engine,
                "analytics_engine": self._config.analytics_engine,
                "portal_engine": self._config.portal_engine,
            },
            "api_prefix": self._config.api_prefix,
            "mobile_prefix": self._config.mobile_prefix,
            "partner_prefix": self._config.partner_prefix,
        }

    def health(self) -> dict:
        from applications.agro_marketplace import agro_marketplace

        app_health = agro_marketplace.health()
        return {
            **self.version_info(),
            "healthy": True,
            "components": {
                "platform": app_health.get("platform"),
                "ecosystem": app_health.get("ecosystem"),
                "export": app_health.get("export"),
                "bi": app_health.get("bi"),
                "portal": app_health.get("portal"),
            },
        }

    async def readiness(self) -> ReadinessSnapshot:
        validation = await self.validation.run_full_validation()
        quality = self.qa.quality_report()
        security = self.qa.security_report()
        performance = self.qa.performance_report()
        blockers = []
        for report in (validation, quality, security):
            if report.failed:
                blockers.append(f"{report.kind.value}:{report.failed}_failed")
        total_checks = validation.passed + validation.failed + validation.warnings
        score = round((validation.passed / total_checks) * 100, 2) if total_checks else 0.0
        ready = (
            validation.ok
            and quality.ok
            and security.ok
            and self._config.application_version == "2.0.0"
            and self._config.application_status == "Production Ready"
        )
        snapshot = ReadinessSnapshot(
            ready=ready,
            score=score,
            checks=[
                {"name": "validation", "ok": validation.ok, "report_id": validation.report_id},
                {"name": "quality", "ok": quality.ok, "report_id": quality.report_id},
                {"name": "security", "ok": security.ok, "report_id": security.report_id},
                {"name": "performance", "ok": performance.ok, "report_id": performance.report_id},
            ],
            blockers=blockers,
        )
        saved = self._store.readiness_snapshots.save(snapshot.snapshot_id, snapshot)
        if saved.ready:
            await publish(
                ProductionReadyEvent(
                    version=self._config.application_version,
                    status=self._config.application_status,
                    score=saved.score,
                )
            )
        return saved

    async def verify_deployment(self) -> dict:
        report = self.qa.deployment_report()
        verified = report.ok
        await publish(
            DeploymentVerifiedEvent(version=self._config.application_version, verified=verified)
        )
        return {"verified": verified, "report": report.to_dict()}

    async def create_release(self, *, notes: str = "") -> ReleaseRecord:
        record = ReleaseRecord(
            version=self._config.application_version,
            status=self._config.application_status,
            release_type=self._config.release,
            notes=notes
            or "Agro Marketplace commercial production release — certified after full validation.",
        )
        saved = self._store.release_records.save(record.release_id, record)
        await publish(
            ReleaseCreatedEvent(
                release_id=saved.release_id,
                version=saved.version,
                release_type=saved.release_type,
            )
        )
        return saved

    async def certify(self, release_id: str | None = None) -> ReleaseRecord:
        readiness = await self.readiness()
        if release_id:
            record = self._store.release_records.get(release_id)
            if record is None:
                record = await self.create_release()
        else:
            record = await self.create_release()
        record.certified = readiness.ready
        saved = self._store.release_records.save(record.release_id, record)
        await publish(
            CertificationCompletedEvent(
                release_id=saved.release_id,
                certified=saved.certified,
                version=saved.version,
            )
        )
        return saved

    async def production_bundle(self) -> dict:
        validation = await self.validation.run_full_validation()
        readiness = await self.readiness()
        release = await self.certify()
        deployment = await self.verify_deployment()
        reports = {
            "production": validation.to_dict(),
            "quality": self.qa.quality_report().to_dict(),
            "security": self.qa.security_report().to_dict(),
            "performance": self.qa.performance_report().to_dict(),
            "compatibility": self.qa.compatibility_report().to_dict(),
            "deployment": deployment["report"],
        }
        return {
            "version": self.version_info(),
            "readiness": readiness.to_dict(),
            "release": release.to_dict(),
            "reports": reports,
            "production_ready": readiness.ready and release.certified,
        }

    def list_releases(self) -> list[ReleaseRecord]:
        return sorted(self._store.release_records.list_all(), key=lambda r: r.created_at, reverse=True)

    def metrics(self) -> dict:
        return {
            "validation_reports": self._store.validation_reports.count(),
            "readiness_snapshots": self._store.readiness_snapshots.count(),
            "releases": self._store.release_records.count(),
        }


ops_engine = OpsEngine()
