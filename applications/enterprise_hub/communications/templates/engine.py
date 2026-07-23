"""Template engine — register and render CRM/Invoice/Lead/... templates."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.communications.models import TEMPLATE_FORMATS, TEMPLATE_KINDS
from applications.enterprise_hub.communications.templates.renderer import render_template
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store

DEFAULT_BODIES = {
    "crm": "Hello {{name}}, CRM update for {{company}} on {{date}}: {{status}}",
    "invoice": "Invoice for {{company}} — {{name}} status {{status}} on {{date}}",
    "lead": "New lead {{name}} for project {{project}} ({{company}})",
    "task": "Task {{name}} on {{project}} due {{date}} — {{status}}",
    "approval": "Approval required: {{name}} / {{project}} — {{status}}",
    "security": "Security alert {{name}} for {{company}} at {{date}}",
    "ai_alert": "AI alert: {{name}} on {{project}} — {{status}}",
    "report": "Report {{name}} for {{company}} covering {{date}}",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class TemplateEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def register(
        self,
        *,
        kind: str,
        name: str,
        body: str = "",
        fmt: str = "plain",
    ) -> dict[str, Any]:
        k = kind.lower().strip()
        if k not in TEMPLATE_KINDS:
            raise ValidationError(f"kind must be one of {list(TEMPLATE_KINDS)}")
        f = (fmt or "plain").lower().strip()
        if f not in TEMPLATE_FORMATS:
            raise ValidationError(f"format must be one of {list(TEMPLATE_FORMATS)}")
        if not name:
            raise ValidationError("name required")
        tid = _id("comm_tpl")
        return self.store.comm_templates.save(
            tid,
            {
                "template_id": tid,
                "kind": k,
                "name": name,
                "body": body or DEFAULT_BODIES.get(k, "{{name}}"),
                "format": f,
                "at": _now(),
            },
        )

    def render(
        self,
        *,
        template_id: str = "",
        kind: str = "",
        variables: dict[str, Any] | None = None,
        fmt: str = "",
    ) -> dict[str, Any]:
        tpl = None
        if template_id:
            tpl = self.store.comm_templates.get(template_id)
            if tpl is None:
                raise NotFoundError(f"template not found: {template_id}")
        elif kind:
            k = kind.lower().strip()
            for item in self.store.comm_templates.list_all():
                if isinstance(item, dict) and item.get("kind") == k:
                    tpl = item
                    break
            if tpl is None:
                body = DEFAULT_BODIES.get(k, "{{name}}")
                rendered = render_template(body, variables, fmt or "plain")
                rid = _id("comm_rend")
                return self.store.comm_renders.save(
                    rid,
                    {
                        "render_id": rid,
                        "kind": k,
                        "format": fmt or "plain",
                        "body": rendered,
                        "variables": variables or {},
                        "at": _now(),
                    },
                )
        else:
            raise ValidationError("template_id or kind required")

        rendered = render_template(
            tpl["body"], variables, fmt or tpl.get("format", "plain")
        )
        rid = _id("comm_rend")
        return self.store.comm_renders.save(
            rid,
            {
                "render_id": rid,
                "template_id": tpl["template_id"],
                "kind": tpl["kind"],
                "format": fmt or tpl.get("format", "plain"),
                "body": rendered,
                "variables": variables or {},
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "templates": self.store.comm_templates.count(),
            "renders": self.store.comm_renders.count(),
            "kinds": list(TEMPLATE_KINDS),
        }
