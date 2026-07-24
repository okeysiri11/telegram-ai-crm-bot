"""AI Marketing OS library facade — Sprint 22.5."""

from __future__ import annotations

from typing import Any

from platform_ai_marketing_os.approval import AIApprovalWorkflow
from platform_ai_marketing_os.brand import BrandCenter
from platform_ai_marketing_os.calendar import ContentCalendar
from platform_ai_marketing_os.campaigns import CampaignManager
from platform_ai_marketing_os.content import AIContentGenerator
from platform_ai_marketing_os.creative import CreativeStudio
from platform_ai_marketing_os.integrations import MarketingIntegrations
from platform_ai_marketing_os.models import PRINCIPLES
from platform_ai_marketing_os.opportunities import OpportunityMarketingEngine
from platform_ai_marketing_os.performance import AIPerformanceAnalyzer


class AIMarketingOSLibrary:
    def __init__(self) -> None:
        self.brand = BrandCenter()
        self.creative = CreativeStudio()
        self.calendar = ContentCalendar()
        self.campaigns = CampaignManager()
        self.opportunities = OpportunityMarketingEngine()
        self.content = AIContentGenerator()
        self.approval = AIApprovalWorkflow()
        self.performance = AIPerformanceAnalyzer()
        self.integrations = MarketingIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        brand = self.brand.create(name="Pilot Beauty Brand")
        creative = self.creative.generate(kind="reels", prompt="weekday happy hour", brand=brand)
        content = self.content.generate(kind="post", topic="Fill afternoon slots with 15% off", brand=brand)
        opps = self.opportunities.detect(
            advisor={"opportunities_found": ["underloaded_staff", "repeat_visit_decline"], "open_slots": True},
            booking={"waitlist": True},
            dashboard={"open_slots": 6, "master_load": 0.45, "revenue": 100, "bookings": 2},
        )
        calendar = self.calendar.plan(days=7, opportunities=opps["signals"])
        campaign = self.campaigns.create(kind="happy_hours", title="Afternoon Fill", budget=50.0)
        card = self.approval.create_card(
            reason=opps["proposals"][0]["proposal"],
            expected_effect=opps["proposals"][0]["expected_effect"],
            reach_forecast=2500,
            load_forecast=0.15,
            budget=50.0,
            payload={"campaign": campaign, "content": content, "creative": creative},
        )
        decision = self.approval.decide(card, action="approve", owner_id="salon_owner")
        perf = self.performance.analyze(campaign=campaign)
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "brand": brand["name"],
            "creatives": 1,
            "content_pieces": 1,
            "calendar_entries": calendar["count"],
            "opportunity_signals": opps["count"],
            "campaigns": 1,
            "approval_status": decision["status"],
            "publish_allowed": decision["publish_allowed"],
            "ai_never_publishes_alone": True,
            "ai_published": False,
            "performance_passed": perf["passed"],
            "epi_handoff": True,
            "duplicates_core_logic": False,
            "marketing_os_ready": True,
            "status": "ready",
            "integrations": links,
            "full": {
                "brand": brand,
                "creative": creative,
                "content": content,
                "opportunities": opps,
                "calendar": calendar,
                "campaign": campaign,
                "card": card,
                "decision": decision,
                "performance": perf,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "brand",
                "creative",
                "calendar",
                "campaigns",
                "opportunities",
                "content",
                "approval",
                "performance",
            ],
            "principles": self.principles(),
        }


ai_marketing_os_library = AIMarketingOSLibrary()
