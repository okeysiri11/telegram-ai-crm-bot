"""AI Marketing OS Suite facade — Sprint 22.5 / v6.6.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_ai_marketing_os.facade import AIMarketingOSLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIMarketingOSSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = AIMarketingOSLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def _signals_context(self) -> dict[str, Any]:
        advisor = {}
        briefs = self.store.aba_briefs.list_all()
        if briefs:
            advisor = briefs[-1]
        dashboard = {}
        dashes = self.store.bos_dashboards.list_all() or self.store.bws_dashboards.list_all()
        if dashes:
            dashboard = dashes[-1]
        booking = {"waitlist": bool(self.store.bcj_waitlist.list_all())}
        return {"advisor": advisor, "dashboard": dashboard, "booking": booking}

    def bootstrap(self) -> dict[str, Any]:
        self.library = AIMarketingOSLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        # Enrich opportunities from live Beauty stack when available
        ctx = self._signals_context()
        if ctx["advisor"] or ctx["dashboard"] or ctx["booking"]["waitlist"]:
            live_opps = self.library.opportunities.detect(**ctx)
            full["opportunities"] = live_opps
            result["opportunity_signals"] = live_opps["count"]
        bid = _id("amo_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.amo_bootstraps.save(bid, record)
        brid = _id("amo_br")
        self.store.amo_brands.save(brid, {"brand_id": brid, **full["brand"], "created_at": _now()})
        cid = _id("amo_cr")
        self.store.amo_creatives.save(cid, {"creative_id": cid, **full["creative"], "created_at": _now()})
        coid = _id("amo_ct")
        self.store.amo_content.save(coid, {"content_id": coid, **full["content"], "created_at": _now()})
        caid = _id("amo_cal")
        self.store.amo_calendars.save(caid, {"calendar_id": caid, **full["calendar"], "created_at": _now()})
        cpid = _id("amo_cp")
        self.store.amo_campaigns.save(cpid, {"campaign_id": cpid, **full["campaign"], "created_at": _now()})
        apid = _id("amo_ap")
        self.store.amo_approvals.save(apid, {"approval_id": apid, **full["decision"], "decided_at": _now()})
        pfid = _id("amo_pf")
        self.store.amo_performance.save(pfid, {"performance_id": pfid, **full["performance"], "analyzed_at": _now()})
        # Hand off to Product Intelligence store as feedback source when possible
        try:
            from applications.enterprise_hub import enterprise_hub

            handoff = full["performance"]["product_intelligence_handoff"]
            enterprise_hub.product_intelligence.ingest(
                source="ai_marketing",
                title=handoff["title"],
                description="Campaign performance handoff",
                module="ai_marketing_os",
                metadata=handoff.get("payload"),
            )
        except Exception:
            pass
        record["brand_id"] = brid
        record["campaign_id"] = cpid
        record["approval_id"] = apid
        record["performance_id"] = pfid
        self.store.amo_bootstraps.save(bid, record)
        return record

    def upsert_brand(self, **kwargs: Any) -> dict[str, Any]:
        try:
            brand = self.library.brand.create(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        brid = _id("amo_br")
        record = {"brand_id": brid, **brand, "created_at": _now()}
        self.store.amo_brands.save(brid, record)
        return record

    def generate_creative(self, *, kind: str, prompt: str, brand_id: str = "") -> dict[str, Any]:
        brand = self.store.amo_brands.get(brand_id) if brand_id else None
        if brand_id and not brand:
            raise NotFoundError(f"brand not found: {brand_id}")
        try:
            creative = self.library.creative.generate(kind=kind, prompt=prompt, brand=brand)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        cid = _id("amo_cr")
        record = {"creative_id": cid, "brand_id": brand_id or None, **creative, "created_at": _now()}
        self.store.amo_creatives.save(cid, record)
        return record

    def generate_content(self, *, kind: str, topic: str, brand_id: str = "") -> dict[str, Any]:
        brand = self.store.amo_brands.get(brand_id) if brand_id else None
        try:
            content = self.library.content.generate(kind=kind, topic=topic, brand=brand)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        coid = _id("amo_ct")
        record = {"content_id": coid, "brand_id": brand_id or None, **content, "created_at": _now()}
        self.store.amo_content.save(coid, record)
        return record

    def detect_opportunities(self) -> dict[str, Any]:
        ctx = self._signals_context()
        result = self.library.opportunities.detect(**ctx)
        oid = _id("amo_opp")
        record = {"opportunity_id": oid, **result, "detected_at": _now()}
        self.store.amo_opportunities.save(oid, record)
        return record

    def create_campaign(self, **kwargs: Any) -> dict[str, Any]:
        try:
            campaign = self.library.campaigns.create(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        cpid = _id("amo_cp")
        record = {"campaign_id": cpid, **campaign, "created_at": _now()}
        self.store.amo_campaigns.save(cpid, record)
        return record

    def submit_for_approval(self, *, campaign_id: str, reason: str = "") -> dict[str, Any]:
        campaign = self.store.amo_campaigns.get(campaign_id)
        if not campaign:
            raise NotFoundError(f"campaign not found: {campaign_id}")
        card = self.library.approval.create_card(
            reason=reason or f"Launch {campaign.get('title')}",
            expected_effect={"bookings_lift": 0.1},
            budget=float(campaign.get("budget") or 0),
            payload={"campaign_id": campaign_id},
        )
        apid = _id("amo_ap")
        record = {"approval_id": apid, **card, "created_at": _now()}
        self.store.amo_approvals.save(apid, record)
        return record

    def owner_decide(self, *, approval_id: str, action: str, owner_id: str, edits: dict[str, Any] | None = None) -> dict[str, Any]:
        card = self.store.amo_approvals.get(approval_id)
        if not card:
            raise NotFoundError(f"approval card not found: {approval_id}")
        try:
            decision = self.library.approval.decide(card, action=action, owner_id=owner_id, edits=edits)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.amo_approvals.save(approval_id, {**decision, "decided_at": _now()})
        return decision

    def analyze_performance(self, *, campaign_id: str, observed: dict[str, Any] | None = None) -> dict[str, Any]:
        campaign = self.store.amo_campaigns.get(campaign_id)
        if not campaign:
            raise NotFoundError(f"campaign not found: {campaign_id}")
        result = self.library.performance.analyze(campaign=campaign, observed=observed)
        pfid = _id("amo_pf")
        record = {"performance_id": pfid, "campaign_id": campaign_id, **result, "analyzed_at": _now()}
        self.store.amo_performance.save(pfid, record)
        try:
            from applications.enterprise_hub import enterprise_hub

            handoff = result["product_intelligence_handoff"]
            enterprise_hub.product_intelligence.ingest(
                source="ai_marketing",
                title=handoff["title"],
                module="ai_marketing_os",
                metadata=handoff.get("payload"),
            )
        except Exception:
            pass
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.amo_bootstraps.list_all()),
            "brands": len(self.store.amo_brands.list_all()),
            "campaigns": len(self.store.amo_campaigns.list_all()),
            "approvals": len(self.store.amo_approvals.list_all()),
            "performance": len(self.store.amo_performance.list_all()),
        }


ai_marketing_os = AIMarketingOSSuite()
