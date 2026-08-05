# n8n bridge — external workflow orchestration only.
# Platform Runtime remains system of record. No business logic in n8n.

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from platform_integrations.webhook_manager import WebhookManager

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class WorkflowTemplate:
    template_id: str
    name: str
    version: str
    description: str
    trigger: str  # webhook | schedule | manual
    callback_path: str
    tags: list[str] = field(default_factory=list)
    # Platform owns semantics; n8n only orchestrates steps that call platform APIs.
    platform_owned: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "trigger": self.trigger,
            "callback_path": self.callback_path,
            "tags": list(self.tags),
            "platform_owned": self.platform_owned,
            "business_logic_in_n8n": False,
        }


@dataclass
class WorkflowExecution:
    execution_id: str
    workflow_id: str
    template_id: str | None
    status: str  # pending | running | success | failed | cancelled
    source: str  # n8n | platform
    started_at: str
    finished_at: str | None = None
    callback_payload: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    version: str = "1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "template_id": self.template_id,
            "status": self.status,
            "source": self.source,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "callback_payload": dict(self.callback_payload),
            "error": self.error,
            "version": self.version,
        }


DEFAULT_TEMPLATES: list[dict[str, Any]] = [
    {
        "template_id": "n8n_tpl_lead_notify",
        "name": "Lead → Notify",
        "version": "1.0.0",
        "description": "Webhook lead intake; platform CRM + notifications own state.",
        "trigger": "webhook",
        "callback_path": "/integrations/n8n/callback",
        "tags": ["crm", "comms"],
    },
    {
        "template_id": "n8n_tpl_media_pipeline",
        "name": "Media Pipeline Fan-out",
        "version": "1.0.0",
        "description": "Triggers Production Runtime jobs; n8n does not render media.",
        "trigger": "manual",
        "callback_path": "/integrations/n8n/callback",
        "tags": ["production", "media"],
    },
    {
        "template_id": "n8n_tpl_provider_health",
        "name": "Provider Health Sweep",
        "version": "1.0.0",
        "description": "Calls APH health; Runtime records results.",
        "trigger": "schedule",
        "callback_path": "/integrations/n8n/callback",
        "tags": ["aph", "ops"],
    },
]


class N8nBridge:
    """External orchestration bridge. Credentials via vault refs — never inline secrets."""

    def __init__(self, webhook_manager: WebhookManager | None = None) -> None:
        self._webhooks = webhook_manager or WebhookManager()
        self._templates: dict[str, WorkflowTemplate] = {}
        self._executions: dict[str, WorkflowExecution] = {}
        self._workflow_versions: dict[str, list[str]] = {}
        self._audit: list[dict[str, Any]] = []
        self._oauth_clients: dict[str, dict[str, Any]] = {}
        self._callback_secret = secrets.token_hex(24)
        for raw in DEFAULT_TEMPLATES:
            self.register_template(**raw)

    def reset(self) -> None:
        self._templates.clear()
        self._executions.clear()
        self._workflow_versions.clear()
        self._audit.clear()
        self._oauth_clients.clear()
        for raw in DEFAULT_TEMPLATES:
            self.register_template(**raw)

    def register_template(
        self,
        *,
        template_id: str,
        name: str,
        version: str,
        description: str,
        trigger: str,
        callback_path: str,
        tags: list[str] | None = None,
    ) -> WorkflowTemplate:
        tpl = WorkflowTemplate(
            template_id=template_id,
            name=name,
            version=version,
            description=description,
            trigger=trigger,
            callback_path=callback_path,
            tags=list(tags or []),
            platform_owned=True,
        )
        self._templates[template_id] = tpl
        versions = self._workflow_versions.setdefault(template_id, [])
        if version not in versions:
            versions.append(version)
        self._audit_log("template_registered", {"template_id": template_id, "version": version})
        return tpl

    def list_templates(self) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self._templates.values()]

    def versions(self, template_id: str) -> list[str]:
        return list(self._workflow_versions.get(template_id, []))

    def register_oauth_client(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        scopes: list[str] | None = None,
        secret_ref: str = "vault://n8n/oauth_client",
    ) -> dict[str, Any]:
        record = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scopes": list(scopes or ["workflow:execute", "webhook:write"]),
            "secret_ref": secret_ref,
            "registered_at": _now(),
        }
        self._oauth_clients[client_id] = record
        self._audit_log("oauth_registered", {"client_id": client_id})
        return dict(record)

    def ensure_webhook(self, *, name: str = "n8n-callback") -> dict[str, Any]:
        existing = [w for w in self._webhooks.list_webhooks() if w.provider == "n8n"]
        if existing:
            reg = existing[0]
        else:
            reg = self._webhooks.register(
                name=name,
                provider="n8n",
                path="/integrations/n8n/callback",
            )
        return {
            "webhook_id": reg.webhook_id,
            "path": reg.path,
            "provider": reg.provider,
            "secret_hint": reg.secret[:8] + "…",
        }

    def start_execution(
        self,
        *,
        workflow_id: str,
        template_id: str | None = None,
        source: str = "n8n",
        version: str = "1",
    ) -> WorkflowExecution:
        ex = WorkflowExecution(
            execution_id=f"n8n_ex_{uuid.uuid4().hex[:12]}",
            workflow_id=workflow_id,
            template_id=template_id,
            status="running",
            source=source,
            started_at=_now(),
            version=version,
        )
        self._executions[ex.execution_id] = ex
        self._audit_log(
            "execution_started",
            {"execution_id": ex.execution_id, "workflow_id": workflow_id, "source": source},
        )
        return ex

    def verify_callback_signature(self, *, body: bytes, signature: str, secret: str | None = None) -> bool:
        key = (secret or self._callback_secret).encode("utf-8")
        digest = hmac.new(key, body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(digest, signature or "")

    def handle_callback(
        self,
        *,
        execution_id: str | None,
        workflow_id: str,
        status: str,
        payload: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Execution callback from n8n — records history; does not apply domain mutations."""
        if execution_id and execution_id in self._executions:
            ex = self._executions[execution_id]
        else:
            ex = self.start_execution(workflow_id=workflow_id, source="n8n")
        ex.status = status if status in {"success", "failed", "cancelled", "running"} else "failed"
        ex.finished_at = _now()
        ex.callback_payload = dict(payload or {})
        ex.error = error
        self._audit_log(
            "execution_callback",
            {
                "execution_id": ex.execution_id,
                "status": ex.status,
                "workflow_id": workflow_id,
                "platform_applies_business_logic": True,
                "n8n_applies_business_logic": False,
            },
        )
        return ex.to_dict()

    def list_executions(self, *, limit: int = 50) -> list[dict[str, Any]]:
        items = sorted(self._executions.values(), key=lambda e: e.started_at, reverse=True)
        return [e.to_dict() for e in items[:limit]]

    def monitor(self) -> dict[str, Any]:
        statuses: dict[str, int] = {}
        for e in self._executions.values():
            statuses[e.status] = statuses.get(e.status, 0) + 1
        return {
            "templates": len(self._templates),
            "executions": len(self._executions),
            "by_status": statuses,
            "oauth_clients": len(self._oauth_clients),
            "system_of_record": "platform_runtime",
            "external_orchestrator": "n8n",
            "business_logic_in_n8n": False,
        }

    def audit_log(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return list(self._audit[-limit:])

    def _audit_log(self, action: str, detail: dict[str, Any]) -> None:
        self._audit.append({"at": _now(), "action": action, "detail": detail, "ts": time.time()})
        logger.info("n8n_bridge action=%s detail=%s", action, detail)


n8n_bridge = N8nBridge()
