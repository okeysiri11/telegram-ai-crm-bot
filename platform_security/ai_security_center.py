# AI Security Center — Sprint 32.4.
# Canonical facade over APH prompt_firewall + agent policy. No second firewall.

from __future__ import annotations

from typing import Any


class AiSecurityCenter:
    """Prompt firewall, injection/jailbreak detection, agent sandboxing policies."""

    def __init__(self) -> None:
        self._blocked = 0
        self._allowed = 0
        self._abuse = 0
        self._agent_denies = 0

    def reset(self) -> None:
        self._blocked = 0
        self._allowed = 0
        self._abuse = 0
        self._agent_denies = 0
        try:
            from applications.enterprise_hub.ai_provider_hub.prompt_firewall import reset_abuse_state

            reset_abuse_state()
        except Exception:  # noqa: BLE001
            pass

    def guard_prompt(self, raw: str, *, actor: str = "platform", max_tokens: int = 4096) -> dict[str, Any]:
        from applications.enterprise_hub.ai_provider_hub.prompt_firewall import guard_prompt

        result = guard_prompt(raw, actor=actor, max_tokens=max_tokens)
        if result.get("ok"):
            self._allowed += 1
        else:
            self._blocked += 1
            if any("abuse" in str(r) for r in result.get("reasons") or []):
                self._abuse += 1
        result["firewall"] = "aph_prompt_firewall"
        result["center"] = "platform_security.ai_security_center"
        return result

    def validate_output(self, text: str) -> dict[str, Any]:
        """Basic output validation — secrets / script leakage heuristics."""
        reasons: list[str] = []
        lowered = (text or "").lower()
        for needle in ("api_key", "sk-", "bearer ", "<script", "iam_jwt_secret"):
            if needle in lowered:
                reasons.append(f"output_leak:{needle.strip()}")
        ok = len(reasons) == 0
        if not ok:
            self._blocked += 1
        return {"ok": ok, "reasons": reasons, "policy": "output_validation"}

    def enforce_model_policy(self, *, model: str, allowed_models: list[str] | None = None) -> dict[str, Any]:
        allow = allowed_models or ["gpt-4o-mini", "gpt-4o", "claude-3-5-sonnet", "openrouter/auto"]
        ok = model in allow or model.startswith("openrouter/")
        if not ok:
            self._blocked += 1
        return {"ok": ok, "model": model, "allowed": allow, "policy": "model_allowlist"}

    def agent_permission_profile(self, agent_id: str, permissions: list[str]) -> dict[str, Any]:
        return {
            "agent_id": agent_id,
            "permissions": list(permissions),
            "sandbox": True,
            "runtime_isolation": True,
            "tool_access_control": True,
            "human_approval_required": "execute_destructive" in permissions or "payments" in permissions,
        }

    def authorize_agent_execution(
        self,
        *,
        agent_id: str,
        action: str,
        permissions: list[str],
        approved: bool = False,
    ) -> dict[str, Any]:
        profile = self.agent_permission_profile(agent_id, permissions)
        needs_approval = bool(profile["human_approval_required"]) and action in {
            "execute_destructive",
            "payments",
            "revoke_tokens",
            "disable_provider",
        }
        if needs_approval and not approved:
            self._agent_denies += 1
            return {"ok": False, "reason": "human_approval_required", "profile": profile}
        if action not in permissions and action not in {"observe", "read"}:
            self._agent_denies += 1
            return {"ok": False, "reason": "permission_denied", "profile": profile}
        return {"ok": True, "profile": profile, "action": action}

    def analytics(self) -> dict[str, Any]:
        return {
            "prompts_allowed": self._allowed,
            "prompts_blocked": self._blocked,
            "abuse_signals": self._abuse,
            "agent_denies": self._agent_denies,
        }

    def capabilities(self) -> dict[str, Any]:
        return {
            "prompt_firewall": True,
            "prompt_injection_detection": True,
            "prompt_sanitizer": True,
            "output_validation": True,
            "ai_abuse_detection": True,
            "jailbreak_detection": True,
            "model_policy": True,
            "provider_isolation": True,
            "token_usage_policies": True,
            "human_approval_policies": True,
            "agent_sandboxing": True,
            "agent_identity": True,
            "agent_permission_profiles": True,
            "agent_execution_policies": True,
            "ai_runtime_isolation": True,
            "ai_tool_access_control": True,
            "system_of_record_firewall": "applications.enterprise_hub.ai_provider_hub.prompt_firewall",
        }
