# PortalEngine — role portals for farmer, buyer, supplier, exporter, admin, executive.

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.analytics.service import AnalyticsService, analytics_service
from applications.agro_marketplace.calendar.service import CalendarService, calendar_service
from applications.agro_marketplace.dashboards.service import DashboardsService, dashboards_service
from applications.agro_marketplace.documents.portal_service import PortalDocumentsService, portal_documents_service
from applications.agro_marketplace.messaging.service import MessagingService, messaging_service
from applications.agro_marketplace.notifications.center import NotificationCenter, notification_center
from applications.agro_marketplace.portal.ai_integration import PortalAIIntegration, portal_ai
from applications.agro_marketplace.portal.models import PortalKind, PortalUser, PortalView
from applications.agro_marketplace.shared.store import AgroStore, agro_store
from applications.agro_marketplace.users.service import UsersService, users_service


class PortalEngine:
    def __init__(
        self,
        store: AgroStore | None = None,
        users: UsersService | None = None,
        notifications: NotificationCenter | None = None,
        messaging: MessagingService | None = None,
        calendar: CalendarService | None = None,
        documents: PortalDocumentsService | None = None,
        dashboards: DashboardsService | None = None,
        analytics: AnalyticsService | None = None,
        ai: PortalAIIntegration | None = None,
    ) -> None:
        self._store = store or agro_store
        self.users = users or users_service
        self.notifications = notifications or notification_center
        self.messaging = messaging or messaging_service
        self.calendar = calendar or calendar_service
        self.documents = documents or portal_documents_service
        self.dashboards = dashboards or dashboards_service
        self.analytics = analytics or analytics_service
        self._ai = ai or portal_ai

    async def register_user(self, user: PortalUser) -> PortalUser:
        saved = await self.users.register(user)
        await self.notifications.send(
            saved.user_id,
            "Welcome",
            f"Welcome to Agro Marketplace, {saved.display_name}",
            channel="in_app",
        )
        return saved

    async def build_portal(self, kind: PortalKind, *, user_id: str = "") -> PortalView:
        builders = {
            PortalKind.FARMER: self.farmer_portal,
            PortalKind.BUYER: self.buyer_portal,
            PortalKind.SUPPLIER: self.supplier_portal,
            PortalKind.EXPORTER: self.exporter_portal,
            PortalKind.ADMINISTRATOR: self.administrator_portal,
            PortalKind.EXECUTIVE: self.executive_portal,
        }
        return await builders[kind](user_id=user_id)

    async def farmer_portal(self, *, user_id: str = "") -> PortalView:
        recs = await self._ai.recommendation_widgets("farmer", user_id)
        chat_hint = await self._ai.chat("Show farmer home tips", role="farmer", user_id=user_id)
        view = PortalView(
            kind=PortalKind.FARMER,
            title="Farmer Portal",
            user_id=user_id,
            widgets=[
                {"type": "harvest", "data": self.analytics.harvest_analytics()},
                {"type": "crops", "data": self.analytics.crop_analytics()},
                {"type": "assistant", "data": chat_hint},
                {"type": "notifications", "count": len(self.notifications.inbox(user_id)) if user_id else 0},
            ],
            recommendations=recs,
        )
        return self._store.portal_views.save(view.view_id, view)

    async def buyer_portal(self, *, user_id: str = "") -> PortalView:
        recs = await self._ai.recommendation_widgets("buyer", user_id)
        view = PortalView(
            kind=PortalKind.BUYER,
            title="Buyer Portal",
            user_id=user_id,
            widgets=[
                {"type": "demand", "data": self.analytics.demand_analytics()},
                {"type": "pricing", "data": self.analytics.pricing_analytics()},
            ],
            recommendations=recs,
        )
        return self._store.portal_views.save(view.view_id, view)

    async def supplier_portal(self, *, user_id: str = "") -> PortalView:
        view = PortalView(
            kind=PortalKind.SUPPLIER,
            title="Supplier Portal",
            user_id=user_id,
            widgets=[
                {"type": "supply", "data": self.analytics.supply_analytics()},
                {"type": "sales", "data": self.analytics.sales_analytics()},
            ],
            recommendations=await self._ai.recommendation_widgets("supplier", user_id),
        )
        return self._store.portal_views.save(view.view_id, view)

    async def exporter_portal(self, *, user_id: str = "") -> PortalView:
        view = PortalView(
            kind=PortalKind.EXPORTER,
            title="Exporter Portal",
            user_id=user_id,
            widgets=[
                {"type": "export", "data": self.analytics.export_analytics()},
                {"type": "regional", "data": self.analytics.regional_analytics()},
            ],
            recommendations=await self._ai.recommendation_widgets("exporter", user_id),
        )
        return self._store.portal_views.save(view.view_id, view)

    async def administrator_portal(self, *, user_id: str = "") -> PortalView:
        view = PortalView(
            kind=PortalKind.ADMINISTRATOR,
            title="Administrator Portal",
            user_id=user_id,
            widgets=[
                {"type": "metrics", "data": self.analytics.dashboard_metrics()},
                {"type": "users", "count": self._store.portal_users.count()},
                {"type": "partners", "count": self._store.partner_connections.count()},
            ],
        )
        return self._store.portal_views.save(view.view_id, view)

    async def executive_portal(self, *, user_id: str = "") -> PortalView:
        dash = await self.dashboards.executive()
        recs = await self._ai.recommendation_widgets("executive", user_id)
        view = PortalView(
            kind=PortalKind.EXECUTIVE,
            title="Executive Dashboard Portal",
            user_id=user_id,
            widgets=[
                {"type": "executive_dashboard", "data": dash.to_dict()},
                {"type": "ai", "data": self.analytics.ai_insights()},
            ],
            recommendations=recs,
        )
        return self._store.portal_views.save(view.view_id, view)

    async def assistant(self, message: str, *, role: str = "farmer", user_id: str = "") -> dict[str, Any]:
        return await self._ai.chat(message, role=role, user_id=user_id)

    def metrics(self) -> dict[str, Any]:
        return {
            "users": self._store.portal_users.count(),
            "portal_views": self._store.portal_views.count(),
            "mobile_sessions": self._store.mobile_sessions.count(),
            "partners": self._store.partner_connections.count(),
            "messages": self._store.messages.count(),
            "notifications": self.notifications.metrics(),
        }


portal_engine = PortalEngine()
