"""Sprint 31.2 — Integration Hub / n8n bridge / extended providers.

Naming note: Legal Pilot also uses Sprint 31.2 — this file covers the
Integration Hub deepen track only.
"""

from __future__ import annotations

from platform_integrations.extended_provider_catalog import (
    EXTENDED_PROVIDER_CATALOG,
    catalog_summary,
    list_providers,
)
from platform_integrations.models import ProviderType
from platform_integrations.n8n_bridge import N8nBridge
from platform_integrations.webhook_manager import WebhookManager
from platform_enterprise_ai_provider_hub.models import PROVIDER_KINDS
from platform_enterprise_ai_provider_hub.facade import AIProviderHubLibrary


def test_extended_catalog_covers_required_categories():
    summary = catalog_summary()
    assert summary["total"] >= 50
    for cat in ("ai", "image", "video", "audio", "automation", "crm", "storage", "payments", "observability"):
        assert cat in summary["by_category"]
    assert EXTENDED_PROVIDER_CATALOG["n8n"]["business_logic"] is False
    assert EXTENDED_PROVIDER_CATALOG["n8n"]["system_of_record"] == "platform_runtime"
    ai = list_providers(category="ai")
    ids = {p["provider_id"] for p in ai}
    for required in ("openai", "anthropic", "google_gemini", "openrouter", "deepseek", "mistral", "groq", "xai", "ollama", "litellm"):
        assert required in ids


def test_provider_type_includes_n8n_and_gateways():
    assert ProviderType.N8N.value == "n8n"
    assert ProviderType.LITELLM.value == "litellm"
    assert ProviderType.OPENROUTER.value == "openrouter"


def test_n8n_bridge_templates_webhook_callbacks_and_audit():
    wh = WebhookManager()
    bridge = N8nBridge(webhook_manager=wh)
    bridge.reset()
    templates = bridge.list_templates()
    assert len(templates) >= 3
    assert all(t["platform_owned"] and not t["business_logic_in_n8n"] for t in templates)

    hook = bridge.ensure_webhook()
    assert hook["provider"] == "n8n"
    assert "/integrations/n8n" in hook["path"]

    oauth = bridge.register_oauth_client(client_id="n8n_demo", redirect_uri="http://localhost:5678/oauth")
    assert oauth["secret_ref"].startswith("vault://")

    ex = bridge.start_execution(workflow_id="wf_demo", template_id="n8n_tpl_lead_notify")
    assert ex.status == "running"
    done = bridge.handle_callback(
        execution_id=ex.execution_id,
        workflow_id="wf_demo",
        status="success",
        payload={"event": "lead.created"},
    )
    assert done["status"] == "success"
    assert done["finished_at"]

    mon = bridge.monitor()
    assert mon["system_of_record"] == "platform_runtime"
    assert mon["business_logic_in_n8n"] is False
    assert mon["executions"] >= 1
    assert bridge.versions("n8n_tpl_lead_notify") == ["1.0.0"]
    assert any(a["action"] == "execution_callback" for a in bridge.audit_log())


def test_n8n_callback_signature():
    bridge = N8nBridge()
    body = b'{"ok":true}'
    import hashlib
    import hmac

    secret = "test-secret"
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert bridge.verify_callback_signature(body=body, signature=sig, secret=secret)
    assert not bridge.verify_callback_signature(body=body, signature="bad", secret=secret)


def test_aph_bootstrap_registers_expanded_ai_providers():
    lib = AIProviderHubLibrary()
    result = lib.bootstrap()
    assert result["via_hub_only"] is True
    assert "openrouter" in PROVIDER_KINDS
    assert "litellm" in PROVIDER_KINDS
    assert "groq" in PROVIDER_KINDS
    providers = result["full"]["providers"]
    kinds = {p["kind"] for p in providers}
    for k in ("openai", "anthropic", "google_gemini", "openrouter", "deepseek", "mistral", "groq", "xai", "ollama", "litellm"):
        assert k in kinds
    assert result["full"]["fallback"]  # chain includes litellm-first failover
