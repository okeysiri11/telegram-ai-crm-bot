# User resolver — Sprint 34.2A.
# Resolves any client credential to a single users.id UUID + identity links.

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from database.models.user_identity_link import UserIdentityLink
from database.models.users import User
from database.session import get_session
from platform_identity.identity_links import IdentityProvider
from repositories.users_repository import UsersRepository

logger = logging.getLogger(__name__)


class UserResolver:
    """Identity Core lookup — never invent synthetic telegram_ids here."""

    async def resolve_by_telegram(self, telegram_id: int) -> User | None:
        async with get_session() as session:
            return await UsersRepository(session).get_by_telegram_id(telegram_id)

    async def resolve_by_link(self, provider: str, external_id: str) -> User | None:
        async with get_session() as session:
            result = await session.execute(
                select(UserIdentityLink).where(
                    UserIdentityLink.provider == provider,
                    UserIdentityLink.external_id == str(external_id),
                )
            )
            link = result.scalar_one_or_none()
            if link is None:
                return None
            return await UsersRepository(session).get_by_id(link.user_id)

    async def resolve_by_email(self, email: str) -> User | None:
        email_n = email.strip().lower()
        async with get_session() as session:
            result = await session.execute(select(User).where(User.email == email_n))
            user = result.scalar_one_or_none()
            if user is not None:
                return user
            return await self.resolve_by_link(IdentityProvider.EMAIL.value, email_n)

    async def ensure_telegram_user(
        self,
        telegram_id: int,
        *,
        username: str | None = None,
        full_name: str | None = None,
    ) -> dict[str, Any]:
        """Ensure users row + telegram identity link. Returns canonical snapshot."""
        async with get_session() as session:
            repo = UsersRepository(session)
            user = await repo.ensure_user(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
            )
            if user.display_name is None and (full_name or user.full_name):
                user.display_name = full_name or user.full_name
            await self._ensure_link(
                session,
                user_id=user.id,
                provider=IdentityProvider.TELEGRAM.value,
                external_id=str(telegram_id),
            )
            await session.flush()
            return self.canonical_snapshot(user)

    async def ensure_email_link(
        self,
        *,
        email: str,
        telegram_id: int | None = None,
        display_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Link email to an existing telegram user, or create a user with email only.
        Used by Web login_proof path — preserves existing telegram accounts.
        """
        email_n = email.strip().lower()
        async with get_session() as session:
            repo = UsersRepository(session)
            user: User | None = None

            # Prefer existing email link / column
            result = await session.execute(select(User).where(User.email == email_n))
            user = result.scalar_one_or_none()
            if user is None:
                link_user = await session.execute(
                    select(UserIdentityLink).where(
                        UserIdentityLink.provider == IdentityProvider.EMAIL.value,
                        UserIdentityLink.external_id == email_n,
                    )
                )
                link = link_user.scalar_one_or_none()
                if link is not None:
                    user = await repo.get_by_id(link.user_id)

            if user is None and telegram_id is not None:
                user = await repo.get_by_telegram_id(telegram_id)

            if user is None and telegram_id is not None:
                user = await repo.ensure_user(telegram_id=telegram_id, full_name=display_name)

            if user is None:
                # Email-only account (no synthetic telegram_id).
                user = User(
                    telegram_id=None,
                    email=email_n,
                    display_name=display_name,
                    full_name=display_name,
                    status="active",
                    is_active=True,
                )
                session.add(user)
                await session.flush()
            else:
                if user.email is None:
                    user.email = email_n
                if display_name and not user.display_name:
                    user.display_name = display_name

            await self._ensure_link(
                session,
                user_id=user.id,
                provider=IdentityProvider.EMAIL.value,
                external_id=email_n,
            )
            if user.telegram_id is not None:
                await self._ensure_link(
                    session,
                    user_id=user.id,
                    provider=IdentityProvider.TELEGRAM.value,
                    external_id=str(user.telegram_id),
                )
            await session.flush()
            return self.canonical_snapshot(user)

    async def touch_login(self, user_id: uuid.UUID) -> None:
        try:
            async with get_session() as session:
                user = await UsersRepository(session).get_by_id(user_id)
                if user is None:
                    return
                user.last_login_at = datetime.now(timezone.utc)
                await session.flush()
        except Exception as exc:  # noqa: BLE001 — never break auth on audit write
            logger.debug("touch_login skipped: %s", exc)

    @staticmethod
    async def _ensure_link(session, *, user_id: uuid.UUID, provider: str, external_id: str) -> None:
        result = await session.execute(
            select(UserIdentityLink).where(
                UserIdentityLink.provider == provider,
                UserIdentityLink.external_id == external_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            if existing.user_id != user_id:
                logger.warning(
                    "identity link collision provider=%s external_id=%s existing_user=%s new_user=%s",
                    provider,
                    external_id,
                    existing.user_id,
                    user_id,
                )
            return
        session.add(
            UserIdentityLink(
                user_id=user_id,
                provider=provider,
                external_id=external_id,
                verified_at=datetime.now(timezone.utc),
            )
        )

    @staticmethod
    def canonical_snapshot(user: User) -> dict[str, Any]:
        from platform_identity.registries.workspace_registry import normalize_workspace_codes

        return {
            "id": str(user.id),
            "uuid": str(user.id),
            "telegram_id": user.telegram_id,
            "telegram_username": user.username,
            "email": user.email,
            "phone": user.phone,
            "display_name": user.resolved_display_name,
            "avatar": user.avatar_url,
            "status": user.status or ("active" if user.is_active else "inactive"),
            "roles": [user.role] if user.role else [],
            "companies": [str(user.tenant_id)] if user.tenant_id else [],
            "workspaces": normalize_workspace_codes(list(user.verticals or [])),
            "preferences": dict(user.preferences or {}),
            "created_at": user.created_at.isoformat() if getattr(user, "created_at", None) else None,
            "updated_at": user.updated_at.isoformat() if getattr(user, "updated_at", None) else None,
            "last_login": user.last_login_at.isoformat() if user.last_login_at else None,
        }


user_resolver = UserResolver()
