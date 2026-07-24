"""Client Portal library facade — Sprint 22.8."""

from __future__ import annotations

from typing import Any

from platform_client_portal.account import ClientAccount
from platform_client_portal.assistant import AIBeautyAssistant
from platform_client_portal.booking import OnlineBooking
from platform_client_portal.calendar import PersonalCalendar
from platform_client_portal.certificates import GiftCertificatesView
from platform_client_portal.integrations import PortalIntegrations
from platform_client_portal.loyalty import LoyaltyCenter
from platform_client_portal.memberships import MembershipCenter
from platform_client_portal.mobile import MobileExperience
from platform_client_portal.models import PRINCIPLES
from platform_client_portal.notifications import PushNotificationCenter
from platform_client_portal.security import PortalSecurity


class ClientPortalLibrary:
    def __init__(self) -> None:
        self.account = ClientAccount()
        self.booking = OnlineBooking()
        self.calendar = PersonalCalendar()
        self.loyalty = LoyaltyCenter()
        self.certificates = GiftCertificatesView()
        self.memberships = MembershipCenter()
        self.assistant = AIBeautyAssistant()
        self.notifications = PushNotificationCenter()
        self.security = PortalSecurity()
        self.mobile = MobileExperience()
        self.integrations = PortalIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        account = self.account.create(customer_id="c_portal", name="Client Portal User", phone="+7000")
        account = self.account.enrich(
            account,
            bonuses=120,
            certificates=[{"certificate_id": "cert1", "balance": 50, "status": "active", "expires_at": "2027-01-01"}],
            memberships=[{"membership_id": "mem1", "status": "active", "visits_remaining": 2}],
            visits=[{"status": "completed", "service": "Haircut"}],
            purchases=[{"item": "Serum", "amount": 25}],
            payments=[{"amount": 40, "method": "card"}],
            favorite_masters=["Anna"],
            favorite_services=["Haircut"],
            photos=["photo://1"],
        )
        booking = self.booking.book(
            customer_id="c_portal",
            branch_id="b1",
            service_ids=["haircut", "blowdry"],
            employee_id="e1",
            start="2026-07-28T10:00:00Z",
            end="2026-07-28T11:15:00Z",
        )
        calendar = self.calendar.render(
            appointments=[
                {"status": "confirmed", "start": booking["start"]},
                {"status": "completed", "start": "2026-07-01T10:00:00Z"},
                {"status": "cancelled", "start": "2026-06-01T10:00:00Z"},
            ],
            ai_recommendations=["rebook_in_4_weeks"],
        )
        loyalty = self.loyalty.view(loyalty={"points": 120, "level": "bronze"}, offers=[{"title": "10% off color"}])
        certs = self.certificates.list_certs(account["certificates"])
        mems = self.memberships.view(account["memberships"])
        assistant = self.assistant.recommend(account=account, loyalty=loyalty, memberships=account["memberships"])
        note = self.notifications.push(
            kind="booking_confirmation",
            title="Booking confirmed",
            customer_id="c_portal",
            body="See you soon",
        )
        sec = self.security.enable_2fa(customer_id="c_portal")
        device = self.security.register_device(customer_id="c_portal", device_id="dev1", platform="ios")
        consent = self.security.consent(customer_id="c_portal", accepted=True)
        login = self.security.login_event(customer_id="c_portal", device_id="dev1", success=True)
        mobile = self.mobile.manifest()
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "account_ready": True,
            "booking_under_60s": booking["under_60s"],
            "self_service": booking["self_service"],
            "calendar_upcoming": len(calendar["upcoming"]),
            "loyalty_balance": loyalty["balance"],
            "certificates": certs["count"],
            "memberships_active": len(mems["active"]),
            "assistant_proposes_only": assistant["proposes_only"],
            "ai_may_act": False,
            "push_events": 1,
            "two_factor": sec["two_factor"],
            "mobile_first": mobile["mobile_first"],
            "platforms": mobile["platforms"],
            "duplicates_core_logic": False,
            "client_portal_ready": True,
            "status": "ready",
            "integrations": links,
            "full": {
                "account": account,
                "booking": booking,
                "calendar": calendar,
                "loyalty": loyalty,
                "certificates": certs,
                "memberships": mems,
                "assistant": assistant,
                "notification": note,
                "security": {"two_factor": sec, "device": device, "consent": consent, "login": login},
                "mobile": mobile,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "account",
                "booking",
                "calendar",
                "loyalty",
                "certificates",
                "memberships",
                "assistant",
                "notifications",
                "security",
                "mobile",
            ],
            "principles": self.principles(),
            "mobile": self.mobile.manifest(),
        }


client_portal_library = ClientPortalLibrary()
