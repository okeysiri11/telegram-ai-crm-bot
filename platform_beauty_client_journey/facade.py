"""Beauty Client Journey library facade — Sprint 22.4."""

from __future__ import annotations

from typing import Any

from platform_beauty_client_journey.assistant import AIBookingAssistant
from platform_beauty_client_journey.availability import SmartAvailabilityEngine
from platform_beauty_client_journey.booking import SmartBookingEngine
from platform_beauty_client_journey.integrations import JourneyIntegrations
from platform_beauty_client_journey.journey import CustomerJourney
from platform_beauty_client_journey.loyalty import LoyaltyTriggerEngine
from platform_beauty_client_journey.models import PRINCIPLES
from platform_beauty_client_journey.reminders import ReminderCenter
from platform_beauty_client_journey.waitlist import WaitlistManager


class BeautyClientJourneyLibrary:
    def __init__(self) -> None:
        self.booking = SmartBookingEngine()
        self.journey = CustomerJourney()
        self.availability = SmartAvailabilityEngine()
        self.waitlist = WaitlistManager()
        self.reminders = ReminderCenter()
        self.loyalty = LoyaltyTriggerEngine()
        self.assistant = AIBookingAssistant()
        self.integrations = JourneyIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        journey = self.journey.create(customer_id="c_pilot", source="instagram", first_contact="landing")
        availability = self.availability.suggest(service_ids=["haircut", "blowdry"], duration_min=75)
        assistant = self.assistant.recommend(availability=availability, journey=journey)
        booking = self.booking.book(
            channel="online",
            customer_id="c_pilot",
            service_ids=["haircut", "blowdry"],
            auto_pick=True,
            suggestion=availability["optimal"],
        )
        journey = self.journey.record_event(journey, kind="booking", payload=booking)
        journey = self.journey.record_event(journey, kind="visit", payload={"appointment": "a1"})
        reminders = self.reminders.seed_for_booking(customer_id="c_pilot", appointment_id="a1")
        wait = self.waitlist.join(customer_id="c_wait", service_ids=["manicure"])
        offered = self.waitlist.offer_slot(
            customer_id="c_wait",
            slot={"start": "2026-07-26T16:00:00Z", "end": "2026-07-26T17:00:00Z"},
        )
        loyalty = self.loyalty.detect({**journey, "birthday_today": True, "bonuses": 10, "bonuses_expiring": True})
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "journey_loyalty": journey["loyalty_level"],
            "booking_under_30s": booking["under_30s"],
            "multi_service": booking["multi_service"],
            "availability_suggestions": len(availability["suggestions"]),
            "assistant_proposes_only": assistant["proposes_only"],
            "ai_may_execute": False,
            "reminders": len(reminders),
            "waitlist_offered": offered["offered"],
            "loyalty_triggers": loyalty["count"],
            "marketing_offers": len(loyalty["offers"]),
            "duplicates_core_logic": False,
            "lifecycle_ready": True,
            "status": "ready",
            "integrations": links,
            "full": {
                "journey": journey,
                "availability": availability,
                "assistant": assistant,
                "booking": booking,
                "reminders": reminders,
                "waitlist": wait,
                "offer": offered,
                "loyalty": loyalty,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "booking",
                "journey",
                "availability",
                "waitlist",
                "reminders",
                "loyalty",
                "assistant",
            ],
            "principles": self.principles(),
        }


beauty_client_journey_library = BeautyClientJourneyLibrary()
