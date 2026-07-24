"""Notification Templates — Sprint 22.6."""

from __future__ import annotations

from typing import Any


class NotificationTemplates:
    def __init__(self) -> None:
        self._versions: dict[str, list[dict[str, Any]]] = {}

    def create(
        self,
        *,
        name: str,
        category: str,
        body: str,
        locale: str = "en",
        variables: list[str] | None = None,
    ) -> dict[str, Any]:
        if not name or not body:
            raise ValueError("template name and body are required")
        key = f"{name}:{locale}"
        history = self._versions.setdefault(key, [])
        version = len(history) + 1
        tmpl = {
            "name": name,
            "category": category,
            "body": body,
            "locale": locale,
            "variables": list(variables or []),
            "version": version,
            "preview": body,
        }
        history.append({"version": version, "body": body, "changed": "create" if version == 1 else "update"})
        tmpl["change_history"] = list(history)
        return tmpl

    def preview(self, template: dict[str, Any], *, values: dict[str, Any] | None = None) -> dict[str, Any]:
        values = values or {}
        text = template.get("body", "")
        for k, v in values.items():
            text = text.replace("{{" + k + "}}", str(v))
        return {"preview": text, "locale": template.get("locale"), "version": template.get("version")}
