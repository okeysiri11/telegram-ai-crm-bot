# Session manager — login tracking, activity, revocation.

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from platform_identity.exceptions import SessionError
from platform_identity.models import Principal, SessionRecord

logger = logging.getLogger(__name__)

SESSION_TTL_SECONDS = int(os.getenv("IAM_SESSION_TTL_SECONDS", str(7 * 24 * 3600)))


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionRecord] = {}

    def reset(self) -> None:
        self._sessions.clear()

    def create_session(
        self,
        *,
        principal: Principal,
        ip: str,
        device: str,
        refresh_token_id: str | None = None,
    ) -> SessionRecord:
        session = SessionRecord.new(
            principal=principal,
            ip=ip,
            device=device,
            ttl_seconds=SESSION_TTL_SECONDS,
            refresh_token_id=refresh_token_id,
        )
        self._sessions[session.session_id] = session
        principal.session_id = session.session_id
        logger.info("iam_session_created id=%s user=%s", session.session_id, principal.telegram_id)
        return session

    def get(self, session_id: str) -> SessionRecord:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionError(f"Session {session_id} not found")
        return session

    def touch(self, session_id: str) -> SessionRecord:
        session = self.get(session_id)
        if session.revoked:
            raise SessionError("Session revoked")
        now = datetime.now(timezone.utc)
        if now > session.expires_at:
            raise SessionError("Session expired")
        session.last_activity = now
        return session

    def revoke(self, session_id: str) -> SessionRecord:
        session = self.get(session_id)
        session.revoked = True
        logger.info("iam_session_revoked id=%s", session_id)
        return session

    def revoke_all_for_principal(self, principal_id: str) -> int:
        count = 0
        for session in self._sessions.values():
            if session.principal_id == principal_id and not session.revoked:
                session.revoked = True
                count += 1
        return count

    def list_sessions(self) -> list[SessionRecord]:
        return list(self._sessions.values())

    def active_sessions(self) -> list[SessionRecord]:
        now = datetime.now(timezone.utc)
        return [
            s
            for s in self._sessions.values()
            if not s.revoked and s.expires_at > now
        ]

    def validate(self, session_id: str) -> SessionRecord:
        session = self.touch(session_id)
        return session


session_manager = SessionManager()
