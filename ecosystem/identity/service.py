# Identity service — SSO, sessions, MFA hooks, devices.

from __future__ import annotations

import logging
import time

from events.publisher import publish

from ecosystem.config import DEFAULT_CONFIG
from ecosystem.events import UserLoggedInEvent
from ecosystem.identity.models import (
    Device,
    MFAEnrollment,
    SSOProvider,
    SessionHistoryEntry,
    UnifiedSession,
    UnifiedUser,
    generate_token,
    hash_password,
)
from ecosystem.shared.exceptions import NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store

logger = logging.getLogger(__name__)


class IdentityService:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    def _find_by_email(self, email: str) -> UnifiedUser | None:
        for user in self._store.users.list_all():
            if user.email.lower() == email.lower():
                return user
        return None

    async def register(
        self,
        *,
        email: str,
        password: str,
        display_name: str = "",
    ) -> tuple[UnifiedUser, UnifiedSession]:
        if self._find_by_email(email):
            raise ValidationError("Email already registered")
        user = UnifiedUser(
            email=email,
            password_hash=hash_password(password),
            display_name=display_name or email,
        )
        self._store.users.save(user.user_id, user)
        session = await self._create_session(user)
        return user, session

    async def login(
        self,
        email: str,
        password: str,
        *,
        device_name: str = "",
        platform: str = "",
        ip_address: str = "",
        user_agent: str = "",
    ) -> tuple[UnifiedUser, UnifiedSession]:
        user = self._find_by_email(email)
        if user is None or user.password_hash != hash_password(password):
            raise ValidationError("Invalid credentials")
        if not user.is_active:
            raise ValidationError("Account disabled")
        device = self._register_device(user.user_id, device_name, platform)
        session = await self._create_session(user, device_id=device.device_id)
        self._record_session_history(user.user_id, session.session_id, "login", ip_address, user_agent)
        await publish(UserLoggedInEvent(user_id=user.user_id, session_id=session.session_id, device_id=device.device_id))
        return user, session

    async def sso_login(
        self,
        provider: str,
        external_id: str,
        email: str,
        *,
        display_name: str = "",
    ) -> tuple[UnifiedUser, UnifiedSession]:
        try:
            from ecosystem.integrations.platform_bridge import platform_bridge

            await platform_bridge.authenticate_sso(provider, external_id)
        except Exception:
            logger.debug("sso bridge unavailable")
        user = self._find_by_email(email)
        if user is None:
            user = UnifiedUser(
                email=email,
                display_name=display_name or email,
                sso_provider=SSOProvider(provider) if provider in SSOProvider._value2member_map_ else SSOProvider.OAUTH,
                external_id=external_id,
                password_hash="",
            )
            self._store.users.save(user.user_id, user)
        session = await self._create_session(user)
        self._record_session_history(user.user_id, session.session_id, "sso_login", "", "")
        await publish(UserLoggedInEvent(user_id=user.user_id, session_id=session.session_id))
        return user, session

    async def _create_session(self, user: UnifiedUser, *, device_id: str = "") -> UnifiedSession:
        session = UnifiedSession(
            user_id=user.user_id,
            access_token=generate_token(),
            refresh_token=generate_token(),
            device_id=device_id,
            expires_at=time.time() + DEFAULT_CONFIG.session_ttl_seconds,
        )
        self._store.sessions.save(session.access_token, session)
        return session

    def validate_session(self, access_token: str) -> UnifiedUser | None:
        session = self._store.sessions.get(access_token)
        if session is None or session.expires_at < time.time():
            return None
        return self._store.users.get(session.user_id)

    def get_user(self, user_id: str) -> UnifiedUser:
        user = self._store.users.get(user_id)
        if user is None:
            raise NotFoundError("User", user_id)
        return user

    def list_devices(self, user_id: str) -> list[Device]:
        return [d for d in self._store.devices.list_all() if d.user_id == user_id]

    def trust_device(self, device_id: str) -> Device:
        device = self._store.devices.get(device_id)
        if device is None:
            raise NotFoundError("Device", device_id)
        device.is_trusted = True
        self._store.devices.save(device_id, device)
        return device

    def session_history(self, user_id: str) -> list[SessionHistoryEntry]:
        return sorted(
            [e for e in self._store.session_history.list_all() if e.user_id == user_id],
            key=lambda e: e.created_at,
            reverse=True,
        )

    def enroll_mfa(self, user_id: str, *, method: str = "totp") -> MFAEnrollment:
        user = self.get_user(user_id)
        enrollment = MFAEnrollment(user_id=user_id, method=method, secret_hint="****")
        self._store.mfa_enrollments.save(enrollment.enrollment_id, enrollment)
        return enrollment

    def verify_mfa(self, user_id: str, enrollment_id: str) -> UnifiedUser:
        enrollment = self._store.mfa_enrollments.get(enrollment_id)
        if enrollment is None or enrollment.user_id != user_id:
            raise NotFoundError("MFAEnrollment", enrollment_id)
        enrollment.verified = True
        self._store.mfa_enrollments.save(enrollment_id, enrollment)
        user = self.get_user(user_id)
        user.mfa_enabled = True
        self._store.users.save(user_id, user)
        return user

    def _register_device(self, user_id: str, name: str, platform: str) -> Device:
        device = Device(user_id=user_id, name=name or "Unknown Device", platform=platform or "web")
        self._store.devices.save(device.device_id, device)
        return device

    def _record_session_history(
        self,
        user_id: str,
        session_id: str,
        action: str,
        ip_address: str,
        user_agent: str,
    ) -> None:
        entry = SessionHistoryEntry(
            user_id=user_id,
            session_id=session_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._store.session_history.save(entry.entry_id, entry)


identity_service = IdentityService()
