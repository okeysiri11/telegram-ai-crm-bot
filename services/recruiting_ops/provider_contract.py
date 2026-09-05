"""Common Recruiting provider adapter contract.

Unsupported capabilities return a typed result — they never silently succeed.
"""

from __future__ import annotations

from typing import Any

UNSUPPORTED = "UNSUPPORTED"
NOT_CONFIGURED = "NOT_CONFIGURED"
NOT_CONNECTED = "NOT_CONNECTED"
MOCK_ONLY = "MOCK_ONLY"
LIVE_API_NOT_IMPLEMENTED = "LIVE_API_NOT_IMPLEMENTED"
VALIDATION = "VALIDATION"

CAPABILITIES = (
    "connect",
    "disconnect",
    "health_check",
    "refresh_credentials",
    "list_accounts",
    "list_campaigns",
    "create_campaign",
    "update_campaign",
    "pause_campaign",
    "resume_campaign",
    "fetch_metrics",
    "fetch_leads",
    "send_message",
)

ADS_CAPABILITIES = (
    "connect",
    "disconnect",
    "health_check",
    "refresh_credentials",
    "verify_connection",
    "list_accounts",
    "get_account_info",
    "list_campaigns",
    "get_campaign_metrics",
    "get_account_metrics",
    "get_sync_health",
    "create_campaign",
    "update_campaign",
    "pause_campaign",
    "resume_campaign",
    "fetch_metrics",
    "fetch_leads",
)

MESSAGING_CAPABILITIES = (
    "connect",
    "disconnect",
    "health_check",
    "refresh_credentials",
    "send_message",
)


def adapter_result(
    *,
    ok: bool,
    error: str | None = None,
    message_ru: str | None = None,
    unsupported: bool = False,
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": ok,
        "error": error,
        "message_ru": message_ru,
        "unsupported": unsupported or error == UNSUPPORTED,
        "fake_data": False,
    }
    payload.update(extra)
    return payload


def unsupported(capability: str, provider: str) -> dict[str, Any]:
    return adapter_result(
        ok=False,
        error=UNSUPPORTED,
        unsupported=True,
        capability=capability,
        provider=provider,
        message_ru=f"Возможность {capability} недоступна для {provider}.",
    )


class ProviderAdapter:
    provider = ""
    label = ""
    capabilities: tuple[str, ...] = ()
    mode = "LIVE"

    def supports(self, capability: str) -> bool:
        return capability in self.capabilities

    def invoke(self, capability: str, **kwargs: Any) -> dict[str, Any]:
        if not self.supports(capability):
            return unsupported(capability, self.provider)
        method = getattr(self, capability, None)
        if method is None:
            return unsupported(capability, self.provider)
        return method(**kwargs)
