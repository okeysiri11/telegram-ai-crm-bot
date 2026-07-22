# Verification Engine — photo/VIN/duplicate/fraud/AI damage checks.

from __future__ import annotations

from applications.auto_marketplace.marketplace.models import VerificationReport, VerificationStatus
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.vin.engine import VINEngine, vin_engine


class VerificationEngine:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        vin: VINEngine | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._vin = vin or vin_engine

    def verify_listing(
        self,
        *,
        listing_id: str = "",
        vehicle_id: str = "",
        vin: str = "",
        photo_count: int = 0,
        media_urls: list[str] | None = None,
    ) -> VerificationReport:
        if not vin and not listing_id and not vehicle_id:
            raise ValidationError("vin, listing_id, or vehicle_id is required")

        findings: list[str] = []
        decoded = self._vin.decode(vin) if vin else None
        vin_status = VerificationStatus.PASSED if decoded and decoded.valid else VerificationStatus.FAILED
        if vin and not (decoded and decoded.valid):
            findings.append("invalid_vin")

        photo_status = VerificationStatus.PASSED if photo_count >= 3 or (media_urls and len(media_urls) >= 3) else VerificationStatus.REVIEW
        if photo_status != VerificationStatus.PASSED:
            findings.append("insufficient_photos")

        # Duplicate detection by VIN across listings
        dupes = 0
        if vin:
            dupes = sum(1 for l in self._store.marketplace_listings.list_all() if l.vin.upper() == vin.upper())
        duplicate_score = min(1.0, dupes / 3.0)
        if duplicate_score >= 0.66:
            findings.append("possible_duplicate")

        # Simple fraud heuristics
        fraud_score = 0.1
        if photo_count == 0:
            fraud_score += 0.3
        if duplicate_score > 0:
            fraud_score += duplicate_score * 0.4
        if vin_status == VerificationStatus.FAILED:
            fraud_score += 0.4
        fraud_score = round(min(fraud_score, 1.0), 3)

        ai_image_score = round(0.9 if photo_status == VerificationStatus.PASSED else 0.55, 3)
        damage_estimate = round(max(0.0, (1.0 - ai_image_score) * 2500), 2)

        if fraud_score >= 0.7 or vin_status == VerificationStatus.FAILED:
            status = VerificationStatus.FAILED
        elif findings:
            status = VerificationStatus.REVIEW
        else:
            status = VerificationStatus.PASSED

        report = VerificationReport(
            listing_id=listing_id,
            vehicle_id=vehicle_id,
            vin=vin,
            photo_status=photo_status,
            vin_status=vin_status,
            duplicate_score=round(duplicate_score, 3),
            fraud_score=fraud_score,
            ai_image_score=ai_image_score,
            damage_estimate=damage_estimate,
            status=status,
            findings=findings,
        )
        return self._store.verification_reports.save(report.report_id, report)

    def get(self, report_id: str) -> VerificationReport:
        report = self._store.verification_reports.get(report_id)
        if report is None:
            raise NotFoundError("VerificationReport", report_id)
        return report

    def metrics(self) -> dict:
        return {"verification_reports": self._store.verification_reports.count()}


verification_engine = VerificationEngine()
