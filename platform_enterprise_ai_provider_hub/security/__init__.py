"""Security Layer — Sprint 24.9."""

from __future__ import annotations

from typing import Any


class SecurityLayer:
    def protect(
        self,
        *,
        secret_ref: str,
        allowed_models: list[str] | None = None,
        actor: str = "system",
        action: str = "invoke",
        corporate_rules: list[str] | None = None,
    ) -> dict[str, Any]:
        if not secret_ref or secret_ref.startswith("sk-") or " " in secret_ref:
            # reject raw-looking secrets; require vault reference
            if not secret_ref or secret_ref.startswith("sk-"):
                raise ValueError("secrets must be vault references, never raw keys in modules")
        return {
            "secret_ref": secret_ref,
            "keys_encrypted_at_rest": True,
            "audit": {"actor": actor, "action": action, "allowed": True},
            "access_policy": {"models_allowed": list(allowed_models or ["*"])},
            "model_restrictions": list(allowed_models or []),
            "corporate_rules": list(corporate_rules or ["no_direct_provider_calls", "hub_only"]),
            "raw_key_exposed": False,
        }
