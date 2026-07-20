# PortalEngine — unified Customer Portal, Dealer Portal & Mobile API facade.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.authentication.security import PortalSecurity, portal_security
from applications.auto_marketplace.authentication.service import AuthenticationService, authentication_service
from applications.auto_marketplace.customer_portal.service import CustomerPortalService, customer_portal_service
from applications.auto_marketplace.dealer_portal.service import DealerPortalService, dealer_portal_service
from applications.auto_marketplace.favorites.service import FavoritesService, favorites_service
from applications.auto_marketplace.garage.service import GarageService, garage_service
from applications.auto_marketplace.mobile_api.service import MobileAPIService, mobile_api_service
from applications.auto_marketplace.notifications.portal_service import PortalNotificationService, portal_notification_service
from applications.auto_marketplace.partner_api.service import PartnerAPIService, partner_api_service
from applications.auto_marketplace.profiles.service import ProfileService, profile_service
from applications.auto_marketplace.public_api.service import PublicAPIService, public_api_service
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class PortalEngine:
    """Enterprise Customer Portal, Dealer Portal & Mobile API entry point."""

    def __init__(
        self,
        store: MarketplaceStore | None = None,
        auth: AuthenticationService | None = None,
        profiles: ProfileService | None = None,
        customer: CustomerPortalService | None = None,
        dealer: DealerPortalService | None = None,
        favorites: FavoritesService | None = None,
        garage: GarageService | None = None,
        notifications: PortalNotificationService | None = None,
        mobile: MobileAPIService | None = None,
        public: PublicAPIService | None = None,
        partner: PartnerAPIService | None = None,
        security: PortalSecurity | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self.auth = auth or authentication_service
        self.profiles = profiles or profile_service
        self.customer = customer or customer_portal_service
        self.dealer = dealer or dealer_portal_service
        self.favorites = favorites or favorites_service
        self.garage = garage or garage_service
        self.notifications = notifications or portal_notification_service
        self.mobile = mobile or mobile_api_service
        self.public = public or public_api_service
        self.partner = partner or partner_api_service
        self.security = security or portal_security

    def metrics(self) -> dict[str, Any]:
        return {
            "portal_users": self._store.portal_users.count(),
            "favorites": self._store.favorites.count(),
            "test_drives": self._store.test_drive_bookings.count(),
            "offer_requests": self._store.offer_requests.count(),
            "partner_connections": self._store.partner_connections.count(),
            "portal_notifications": self._store.portal_notifications.count(),
        }


portal_engine = PortalEngine()
