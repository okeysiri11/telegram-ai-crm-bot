# SessionManager — bridge to platform_identity sessions.

from __future__ import annotations

import logging

from platform_security.exceptions import SessionInvalidError
from platform_security.models import SecurityPrincipal

logger = logging.getLogger(__name__)


class SessionManager:
    async def create_session(
        self,
        principal: SecurityPrincipal,
        *,
        ip: str = "0.0.0.0",
        device: str = "unknown",
        ttl_seconds: int = 3600,
    ) -> str:
        try:
            from platform_identity.models import AuthMethod, Principal
            from platform_identity.session_manager import session_manager

            identity = Principal(
                principal_id=principal.principal_id,
                auth_method=AuthMethod.JWT,
                roles=principal.roles,
                permissions=principal.permissions,
            )
            session = session_manager.create_session(
                principal=identity,
                ip=ip,
                device=device,
            )
            principal.session_id = session.session_id
            return session.session_id
        except Exception as exc:
            logger.debug("session bridge unavailable: %s", exc)
            import uuid
            sid = str(uuid.uuid4())
            principal.session_id = sid
            return sid

    def validate(self, session_id: str) -> bool:
        try:
            from platform_identity.session_manager import session_manager

            session = session_manager.get(session_id)
            return session is not None and not session.revoked
        except Exception:
            return bool(session_id)

    def revoke(self, session_id: str) -> None:
        try:
            from platform_identity.session_manager import session_manager

            session_manager.revoke(session_id)
        except Exception as exc:
            logger.debug("session revoke bridge: %s", exc)

    def require_valid(self, session_id: str) -> None:
        if not self.validate(session_id):
            raise SessionInvalidError(session_id)


session_manager = SessionManager()
