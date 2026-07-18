# JWT — access/refresh tokens, rotation, revocation.

from __future__ import annotations

import hashlib
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from platform_identity.exceptions import TokenError
from platform_identity.models import TokenPair

logger = logging.getLogger(__name__)

IAM_JWT_SECRET = os.getenv("IAM_JWT_SECRET", os.getenv("JWT_SECRET", "change-me-in-production"))
IAM_JWT_ALGORITHM = os.getenv("IAM_JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_MINUTES = int(os.getenv("IAM_ACCESS_TOKEN_MINUTES", "15"))
REFRESH_TOKEN_DAYS = int(os.getenv("IAM_REFRESH_TOKEN_DAYS", "7"))


class JwtService:
    def __init__(self) -> None:
        self._revoked_jti: set[str] = set()
        self._refresh_chain: dict[str, str] = {}  # old_jti -> new_jti

    def reset(self) -> None:
        self._revoked_jti.clear()
        self._refresh_chain.clear()

    def issue_tokens(
        self,
        *,
        subject: str,
        roles: list[str],
        permissions: list[str],
        telegram_id: int | None = None,
        session_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> TokenPair:
        now = datetime.now(timezone.utc)
        token_id = str(uuid.uuid4())
        refresh_id = str(uuid.uuid4())

        access_exp = now + timedelta(minutes=ACCESS_TOKEN_MINUTES)
        refresh_exp = now + timedelta(days=REFRESH_TOKEN_DAYS)

        access_payload = self._build_payload(
            subject=subject,
            roles=roles,
            permissions=permissions,
            telegram_id=telegram_id,
            session_id=session_id,
            token_type="access",
            jti=token_id,
            exp=access_exp,
            extra=extra,
        )
        refresh_payload = self._build_payload(
            subject=subject,
            roles=roles,
            permissions=permissions,
            telegram_id=telegram_id,
            session_id=session_id,
            token_type="refresh",
            jti=refresh_id,
            exp=refresh_exp,
            extra={"access_jti": token_id},
        )

        return TokenPair(
            access_token=jwt.encode(access_payload, IAM_JWT_SECRET, algorithm=IAM_JWT_ALGORITHM),
            refresh_token=jwt.encode(refresh_payload, IAM_JWT_SECRET, algorithm=IAM_JWT_ALGORITHM),
            access_expires_at=access_exp,
            refresh_expires_at=refresh_exp,
            session_id=session_id or "",
            token_id=token_id,
        )

    def verify_access_token(self, token: str) -> dict[str, Any]:
        return self._verify(token, expected_type="access")

    def verify_refresh_token(self, token: str) -> dict[str, Any]:
        return self._verify(token, expected_type="refresh")

    def rotate_refresh_token(self, refresh_token: str) -> TokenPair:
        claims = self.verify_refresh_token(refresh_token)
        jti = claims.get("jti")
        if jti in self._revoked_jti:
            raise TokenError("Refresh token revoked")

        self.revoke(jti)

        return self.issue_tokens(
            subject=str(claims.get("sub", "")),
            roles=list(claims.get("roles", [])),
            permissions=list(claims.get("permissions", [])),
            telegram_id=claims.get("telegram_id"),
            session_id=claims.get("session_id"),
        )

    def revoke(self, jti: str | None) -> None:
        if jti:
            self._revoked_jti.add(jti)

    def revoke_token(self, token: str) -> None:
        try:
            claims = jwt.decode(
                token,
                IAM_JWT_SECRET,
                algorithms=[IAM_JWT_ALGORITHM],
                options={"verify_exp": False},
            )
            self.revoke(claims.get("jti"))
        except jwt.PyJWTError as exc:
            raise TokenError(str(exc)) from exc

    def is_revoked(self, jti: str | None) -> bool:
        return jti in self._revoked_jti if jti else False

    def _verify(self, token: str, *, expected_type: str) -> dict[str, Any]:
        try:
            claims = jwt.decode(token, IAM_JWT_SECRET, algorithms=[IAM_JWT_ALGORITHM])
        except jwt.PyJWTError as exc:
            raise TokenError(str(exc)) from exc

        if claims.get("token_type") != expected_type:
            raise TokenError(f"Expected {expected_type} token")

        jti = claims.get("jti")
        if self.is_revoked(jti):
            raise TokenError("Token revoked")

        return claims

    @staticmethod
    def _build_payload(
        *,
        subject: str,
        roles: list[str],
        permissions: list[str],
        telegram_id: int | None,
        session_id: str | None,
        token_type: str,
        jti: str,
        exp: datetime,
        extra: dict[str, Any] | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "sub": subject,
            "roles": roles,
            "permissions": permissions,
            "token_type": token_type,
            "jti": jti,
            "exp": exp,
            "iat": datetime.now(timezone.utc),
        }
        if telegram_id is not None:
            payload["telegram_id"] = telegram_id
        if session_id:
            payload["session_id"] = session_id
        if extra:
            payload.update(extra)
        return payload

    @staticmethod
    def fingerprint(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()[:16]


jwt_service = JwtService()
