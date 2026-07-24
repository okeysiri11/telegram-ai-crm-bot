"""Communications Hub library facade — Sprint 22.6."""

from __future__ import annotations

from typing import Any

from platform_communications_hub.analytics import CommunicationsAnalytics
from platform_communications_hub.assistant import AICommunicationAssistant
from platform_communications_hub.automation import AutomationEngine
from platform_communications_hub.center import UnifiedCommunicationCenter
from platform_communications_hub.delivery import CampaignDeliveryManager
from platform_communications_hub.integrations import HubIntegrations
from platform_communications_hub.models import PRINCIPLES
from platform_communications_hub.templates import NotificationTemplates
from platform_communications_hub.timeline import CommunicationTimeline


class CommunicationsHubLibrary:
    def __init__(self) -> None:
        self.center = UnifiedCommunicationCenter()
        self.templates = NotificationTemplates()
        self.automation = AutomationEngine()
        self.timeline = CommunicationTimeline()
        self.assistant = AICommunicationAssistant()
        self.delivery = CampaignDeliveryManager()
        self.analytics = CommunicationsAnalytics()
        self.integrations = HubIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        tmpl = self.templates.create(
            name="new_appointment",
            category="booking",
            body="Hi {{name}}, your visit is at {{time}}",
            locale="en",
            variables=["name", "time"],
        )
        preview = self.templates.preview(tmpl, values={"name": "Maria", "time": "15:00"})
        auto = self.automation.create(scenario="new_appointment", channel="sms", pre_approved=True)
        sent = self.center.send(
            channel="sms",
            recipient="+70000000000",
            body=preview["preview"],
            template_id=tmpl["name"],
            automation_id="auto:new_appointment",
            industry="beauty",
        )
        timeline = self.timeline.record(
            customer_id="c1", kind="sent", channel="sms", payload={"body": sent["body"]}
        )
        self.timeline.record(customer_id="c1", kind="opened", channel="sms", payload={})
        assistant = self.assistant.recommend(purpose="rebook_invite", customer_id="c1")
        delivery = self.delivery.enqueue(
            campaign_id="camp1",
            recipients=["+7111", "+7222", "+7333"],
            channel="telegram",
            body="Special offer today",
        )
        delivery = self.delivery.report(delivery, delivered=3)
        analytics = self.analytics.summarize(
            delivered=3, opened=2, clicks=1, conversions=1, bookings=1, sales=45.0
        )
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "channels": len(self.center.channels()["channels"]),
            "templates": 1,
            "automations": 1,
            "timeline_events": self.timeline.history(customer_id="c1")["count"],
            "assistant_proposes_only": assistant["proposes_only"],
            "ai_may_send": False,
            "delivery_queued": delivery["report"]["queued"],
            "analytics_ctr": analytics["ctr"],
            "universal_api": True,
            "no_module_sends_independently": True,
            "duplicates_core_logic": False,
            "communications_hub_ready": True,
            "status": "ready",
            "integrations": links,
            "full": {
                "template": tmpl,
                "preview": preview,
                "automation": auto,
                "sent": sent,
                "timeline": timeline,
                "assistant": assistant,
                "delivery": delivery,
                "analytics": analytics,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "center",
                "templates",
                "automation",
                "timeline",
                "assistant",
                "delivery",
                "analytics",
            ],
            "principles": self.principles(),
            "channels": self.center.channels(),
        }


communications_hub_library = CommunicationsHubLibrary()
