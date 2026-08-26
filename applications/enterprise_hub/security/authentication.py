"""Authentication service — Sprint 30.1 Google + local email flows."""

from __future__ import annotations

import hashlib
import secrets
from typing import Any

from applications.enterprise_hub.security.providers import authenticate_provider
from applications.enterprise_hub.security.providers.google import verify_google_id_token
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


DEMO_PASSWORD = "demo"
DEMO_EMAIL_SUFFIXES = ("@demo.corp", "@ados.demo", "@globefly.demo", "@local.dev")
DEMO_SUBJECTS = (
    "owner@demo.corp",
    "ops@demo.corp",
    "owner@ados.demo",
    "admin@ados.demo",
    "travel@globefly.demo",
)


def _hash_password(password: str, *, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()


def is_demo_subject(subject: str) -> bool:
    email = (subject or "").strip().lower()
    if not email or "@" not in email:
        return False
    if email in DEMO_SUBJECTS:
        return True
    return email.endswith(DEMO_EMAIL_SUFFIXES)


class AuthenticationService:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def login(
        self,
        *,
        subject: str,
        provider: str = "local",
        secret: str = "",
    ) -> dict[str, Any]:
        p = provider.lower().strip()
        if p == "google":
            return self.login_google(id_token=secret, subject_hint=subject)
        if p == "local" and secret:
            return self.login_password(subject=subject, password=secret)
        return authenticate_provider(
            self.store, provider=provider, subject=subject, secret=secret
        )

    def login_password(self, *, subject: str, password: str) -> dict[str, Any]:
        from applications.enterprise_hub.security.identity_manager import IdentityManager

        identity_mgr = IdentityManager(self.store)
        identity = identity_mgr.find_by_subject(subject=subject)
        if identity is None:
            event = authenticate_provider(
                self.store, provider="local", subject=subject, secret=""
            )
            event["success"] = False
            event["error"] = "unknown_user"
            self.store.isam_auth_events.save(event["auth_id"], event)
            raise ValidationError("invalid credentials")
        attrs = dict(identity.get("attributes") or {})
        salt = str(attrs.get("password_salt") or "")
        expected = str(attrs.get("password_hash") or "")
        if is_demo_subject(subject):
            if password != DEMO_PASSWORD:
                event = authenticate_provider(
                    self.store, provider="local", subject=subject, secret=""
                )
                event["success"] = False
                event["error"] = "bad_password"
                self.store.isam_auth_events.save(event["auth_id"], event)
                raise ValidationError("invalid credentials")
            self.set_password(subject=subject, password=DEMO_PASSWORD)
            identity = identity_mgr.find_by_subject(subject=subject) or identity
        elif salt and expected:
            if _hash_password(password, salt=salt) != expected:
                event = authenticate_provider(
                    self.store, provider="local", subject=subject, secret=""
                )
                event["success"] = False
                event["error"] = "bad_password"
                self.store.isam_auth_events.save(event["auth_id"], event)
                raise ValidationError("invalid credentials")
        elif not password:
            event = authenticate_provider(
                self.store, provider="local", subject=subject, secret=""
            )
            event["success"] = False
            event["error"] = "bad_password"
            self.store.isam_auth_events.save(event["auth_id"], event)
            raise ValidationError("invalid credentials")
        event = authenticate_provider(
            self.store, provider="local", subject=subject, secret="ok"
        )
        event["identity_id"] = identity["identity_id"]
        event["success"] = True
        self.store.isam_auth_events.save(event["auth_id"], event)
        return {**event, "identity": identity}

    def register_local(
        self,
        *,
        email: str,
        password: str,
        name: str = "",
        role: str = "employee",
    ) -> dict[str, Any]:
        from applications.enterprise_hub.security.identity_manager import IdentityManager

        email_n = email.strip().lower()
        if not email_n or "@" not in email_n:
            raise ValidationError("valid email required")
        if len(password) < 8:
            raise ValidationError("password must be at least 8 characters")
        salt = secrets.token_hex(16)
        identity = IdentityManager(self.store).register_or_get(
            subject=email_n,
            identity_type="user",
            roles=[role],
            attributes={
                "name": name or email_n.split("@")[0],
                "password_salt": salt,
                "password_hash": _hash_password(password, salt=salt),
                "auth_providers": ["local"],
            },
        )
        event = authenticate_provider(
            self.store, provider="local", subject=email_n, secret="register"
        )
        event["action"] = "register"
        event["identity_id"] = identity["identity_id"]
        self.store.isam_auth_events.save(event["auth_id"], event)
        return {"identity": identity, "auth": event}

    def request_password_reset(self, *, email: str) -> dict[str, Any]:
        token = secrets.token_urlsafe(24)
        rid = f"isam_reset_{secrets.token_hex(6)}"
        record = {
            "reset_id": rid,
            "email": email.strip().lower(),
            "token": token,
            "status": "issued",
            "at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
        }
        self.store.isam_audit.save(rid, {**record, "action": "password_reset_request"})
        # Never return raw token in production responses — demo returns token for local tests
        return {"status": "issued", "email": record["email"], "reset_token": token}

    def set_password(self, *, subject: str, password: str) -> dict[str, Any]:
        from applications.enterprise_hub.security.identity_manager import IdentityManager

        email_n = subject.strip().lower()
        if not email_n or "@" not in email_n:
            raise ValidationError("valid email required")
        if not password:
            raise ValidationError("password required")
        identity_mgr = IdentityManager(self.store)
        identity = identity_mgr.register_or_get(
            subject=email_n,
            identity_type="user",
            roles=["company_owner"] if "owner" in email_n else ["employee"],
            attributes={"email": email_n},
        )
        attrs = dict(identity.get("attributes") or {})
        salt = secrets.token_hex(16)
        attrs["password_salt"] = salt
        attrs["password_hash"] = _hash_password(password, salt=salt)
        attrs.setdefault("auth_providers", ["local"])
        identity["attributes"] = attrs
        self.store.isam_identities.save(identity["identity_id"], identity)
        return identity

    def reset_demo_passwords(self, *, password: str = DEMO_PASSWORD) -> list[str]:
        reset: list[str] = []
        for subject in DEMO_SUBJECTS:
            self.set_password(subject=subject, password=password)
            reset.append(subject)
        return reset

    def login_google(
        self,
        *,
        id_token: str,
        subject_hint: str = "",
        default_role: str = "employee",
    ) -> dict[str, Any]:
        from applications.enterprise_hub.security.identity_manager import IdentityManager

        claims = verify_google_id_token(id_token)
        email = claims["email"]
        if subject_hint and subject_hint.strip().lower() not in {email, ""}:
            # hint is advisory only
            pass
        identity_mgr = IdentityManager(self.store)
        existing = identity_mgr.find_by_subject(subject=email)
        if existing is not None:
            attrs = dict(existing.get("attributes") or {})
            providers = list(attrs.get("auth_providers") or [])
            if "google" not in providers:
                providers.append("google")
            attrs.update(
                {
                    "name": claims.get("name") or attrs.get("name"),
                    "picture": claims.get("picture") or attrs.get("picture"),
                    "google_sub": claims.get("sub"),
                    "auth_providers": providers,
                    "email_verified": claims.get("email_verified", True),
                }
            )
            existing["attributes"] = attrs
            existing["email_verified"] = True
            self.store.isam_identities.save(existing["identity_id"], existing)
            identity = existing
        else:
            identity = identity_mgr.register(
                subject=email,
                identity_type="user",
                roles=[default_role],
                attributes={
                    "name": claims.get("name"),
                    "picture": claims.get("picture"),
                    "google_sub": claims.get("sub"),
                    "auth_providers": ["google"],
                    "email_verified": claims.get("email_verified", True),
                },
            )
            identity["email_verified"] = True
            self.store.isam_identities.save(identity["identity_id"], identity)

        event = authenticate_provider(
            self.store, provider="google", subject=email, secret="google"
        )
        event["identity_id"] = identity["identity_id"]
        event["method"] = "google"
        event["claims_mode"] = claims.get("mode")
        event["success"] = True
        self.store.isam_auth_events.save(event["auth_id"], event)
        return {"auth": event, "identity": identity, "claims": claims}

    def status(self) -> dict[str, Any]:
        return {
            "auth_events": self.store.isam_auth_events.count(),
            "providers": ["local", "google", "oauth2", "oidc", "jwt", "microsoft", "apple", "github", "telegram"],
            "preferred": "google",
        }
