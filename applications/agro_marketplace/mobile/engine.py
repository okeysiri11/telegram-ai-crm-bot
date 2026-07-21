# MobileEngine — authentication, profile, and mobile API facade.

from __future__ import annotations

import secrets
import time
from typing import Any

from events.publisher import publish

from applications.agro_marketplace.integrations.ecosystem_bridge import EcosystemBridge, ecosystem_bridge
from applications.agro_marketplace.messaging.service import MessagingService, messaging_service
from applications.agro_marketplace.notifications.center import NotificationCenter, notification_center
from applications.agro_marketplace.portal.ai_integration import PortalAIIntegration, portal_ai
from applications.agro_marketplace.portal.events import MobileSessionStartedEvent
from applications.agro_marketplace.portal.models import MobileSession, PortalUser
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.store import AgroStore, agro_store
from applications.agro_marketplace.users.service import UsersService, users_service


class MobileEngine:
    def __init__(
        self,
        store: AgroStore | None = None,
        users: UsersService | None = None,
        notifications: NotificationCenter | None = None,
        messaging: MessagingService | None = None,
        ai: PortalAIIntegration | None = None,
        ecosystem: EcosystemBridge | None = None,
    ) -> None:
        self._store = store or agro_store
        self.users = users or users_service
        self.notifications = notifications or notification_center
        self.messaging = messaging or messaging_service
        self._ai = ai or portal_ai
        self._ecosystem = ecosystem or ecosystem_bridge

    async def authenticate(
        self,
        *,
        email: str,
        display_name: str = "",
        role: str = "farmer",
        device_id: str = "",
        platform: str = "ios",
        access_token: str = "",
    ) -> dict[str, Any]:
        if not email:
            raise ValidationError("email is required")
        identity = self._ecosystem.validate_identity(access_token) if access_token else None
        user = self.users.get_by_email(email)
        if user is None:
            user = await self.users.register(
                PortalUser(
                    email=email,
                    display_name=display_name or email.split("@")[0],
                    role=role,
                )
            )
        token = access_token or secrets.token_urlsafe(24)
        session = MobileSession(
            user_id=user.user_id,
            device_id=device_id or secrets.token_hex(4),
            access_token=token,
            platform=platform,
            expires_at=time.time() + 86400 * 30,
        )
        saved = self._store.mobile_sessions.save(session.session_id, session)
        await publish(
            MobileSessionStartedEvent(
                session_id=saved.session_id,
                user_id=saved.user_id,
                platform=saved.platform,
            )
        )
        await self.notifications.push(user.user_id, "Signed in", "Mobile session started")
        return {
            "session": saved.to_dict(),
            "user": user.to_dict(),
            "identity": bool(identity),
        }

    def get_session(self, session_id: str) -> MobileSession:
        session = self._store.mobile_sessions.get(session_id)
        if session is None or not session.is_active:
            raise NotFoundError("MobileSession", session_id)
        return session

    def profile(self, user_id: str) -> PortalUser:
        return self.users.get(user_id)

    async def assistant(self, message: str, *, user_id: str = "", role: str = "farmer") -> dict[str, Any]:
        return await self._ai.chat(message, role=role, user_id=user_id)

    def home(self, user_id: str) -> dict[str, Any]:
        user = self.users.get(user_id)
        return {
            "user": user.to_dict(),
            "notifications": [n.to_dict() for n in self.notifications.inbox(user_id)[:20]],
            "threads": [t.to_dict() for t in self.messaging.list_threads(user_id=user_id)],
        }


mobile_engine = MobileEngine()
