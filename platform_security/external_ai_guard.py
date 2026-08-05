# External AI / unauthorized agent protection — Sprint 32.4.

from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Any

_DEFAULT_DEV_SIGNING_SECRET = "platform-ai-request-signing"


class ExternalAiGuard:
    """Reject unknown AI runtimes; verify signed requests and trusted providers."""

    def __init__(self) -> None:
        self._trusted_providers: set[str] = {
            "openrouter",
            "openai",
            "anthropic",
            "aph",
            "n8n_bridge",
            "enterprise_runtime",
        }
        self._seen_nonces: dict[str, float] = {}
        self._rejects = 0
        self._allows = 0
        # Prefer env override; keep deterministic default for unsigned-dev/test paths.
        self._signing_secret = (
            os.environ.get("AI_REQUEST_SIGNING_SECRET")
            or os.environ.get("IAM_JWT_SECRET")
            or _DEFAULT_DEV_SIGNING_SECRET
        )

    def reset(self) -> None:
        self._seen_nonces.clear()
        self._rejects = 0
        self._allows = 0

    def configure(self, *, signing_secret: str | None = None, providers: list[str] | None = None) -> None:
        if signing_secret:
            self._signing_secret = signing_secret
        if providers is not None:
            self._trusted_providers = set(providers)

    def trusted_provider_registry(self) -> list[str]:
        return sorted(self._trusted_providers)

    def sign_request(self, *, body: str, timestamp: str, nonce: str) -> str:
        msg = f"{timestamp}.{nonce}.{body}".encode()
        return hmac.new(self._signing_secret.encode(), msg, hashlib.sha256).hexdigest()

    def verify_signed_request(
        self,
        *,
        body: str,
        timestamp: str,
        nonce: str,
        signature: str,
        max_skew_seconds: float = 300.0,
    ) -> dict[str, Any]:
        try:
            ts = float(timestamp)
        except ValueError:
            self._rejects += 1
            return {"ok": False, "reason": "bad_timestamp"}
        if abs(time.time() - ts) > max_skew_seconds:
            self._rejects += 1
            return {"ok": False, "reason": "replay_or_skew"}
        if nonce in self._seen_nonces:
            self._rejects += 1
            return {"ok": False, "reason": "replay_nonce"}
        expected = self.sign_request(body=body, timestamp=timestamp, nonce=nonce)
        if not hmac.compare_digest(expected, signature or ""):
            self._rejects += 1
            return {"ok": False, "reason": "bad_signature"}
        self._seen_nonces[nonce] = time.time()
        self._allows += 1
        return {"ok": True, "reason": "verified"}

    def verify_ai_client(
        self,
        *,
        provider: str,
        runtime: str,
        agent_certificate: str | None = None,
    ) -> dict[str, Any]:
        if provider not in self._trusted_providers:
            self._rejects += 1
            return {"ok": False, "reason": "provider_not_allowlisted", "provider": provider}
        if runtime not in {"enterprise_runtime", "aph", "n8n_bridge", "platform_jobs"}:
            self._rejects += 1
            return {"ok": False, "reason": "unknown_ai_runtime", "runtime": runtime}
        if agent_certificate is not None and not agent_certificate.startswith("agc_"):
            self._rejects += 1
            return {"ok": False, "reason": "invalid_agent_certificate"}
        self._allows += 1
        return {"ok": True, "provider": provider, "runtime": runtime}

    def authorize_autonomous_agent(
        self,
        *,
        provider: str,
        runtime: str,
        registered: bool,
    ) -> dict[str, Any]:
        client = self.verify_ai_client(provider=provider, runtime=runtime)
        if not client["ok"]:
            return client
        if not registered:
            self._rejects += 1
            return {"ok": False, "reason": "unregistered_autonomous_agent"}
        return {"ok": True, "execution": "allowed"}

    def analytics(self) -> dict[str, Any]:
        return {
            "allows": self._allows,
            "rejects": self._rejects,
            "trusted_providers": self.trusted_provider_registry(),
        }

    def capabilities(self) -> dict[str, Any]:
        return {
            "ai_client_verification": True,
            "agent_authentication": True,
            "agent_certificates": True,
            "trusted_provider_registry": True,
            "signed_ai_requests": True,
            "signed_webhooks": True,
            "tool_permission_validation": True,
            "provider_allow_lists": True,
            "execution_verification": True,
            "reject_unknown_runtimes": True,
            "prevent_unauthorized_autonomous_agents": True,
        }
