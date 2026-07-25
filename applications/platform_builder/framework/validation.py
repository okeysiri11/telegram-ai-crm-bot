"""Validation Framework — Sprint 28.5."""

from __future__ import annotations

from typing import Any

from applications.platform_builder.framework.catalogs import VALIDATION_RULES


class ValidationFramework:
    """Required fields, duplicates, registry, dependencies, knowledge, relationships, live errors, suggestions."""

    def __init__(self) -> None:
        self.rule_ids = [r["id"] for r in VALIDATION_RULES]

    def validate(
        self,
        *,
        draft: dict[str, Any],
        required: list[str] | None = None,
        existing_names: list[str] | None = None,
        dependencies: list[str] | None = None,
        knowledge_topics: list[str] | None = None,
        relationships: dict[str, Any] | None = None,
        registry_ok: bool = True,
    ) -> dict[str, Any]:
        errors: list[dict[str, str]] = []
        suggestions: list[str] = []
        required = required or ["name", "builder_type"]
        existing_names = [n.lower() for n in (existing_names or [])]
        dependencies = dependencies or []
        knowledge_topics = knowledge_topics or []
        relationships = relationships or {}

        for field in required:
            value = draft.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(
                    {
                        "rule": "required_fields",
                        "field": field,
                        "message": f"{field} is required",
                    }
                )
                suggestions.append(f"Provide a value for «{field}».")

        name = (draft.get("name") or "").strip().lower()
        if name and name in existing_names:
            errors.append(
                {
                    "rule": "duplicate_detection",
                    "field": "name",
                    "message": f"Name «{draft.get('name')}» already exists",
                }
            )
            suggestions.append("Choose a unique builder or template name.")

        if not registry_ok:
            errors.append(
                {
                    "rule": "registry_validation",
                    "field": "registry",
                    "message": "Builder Registry rejected this configuration",
                }
            )

        missing_deps = [d for d in dependencies if not d]
        if missing_deps:
            errors.append(
                {
                    "rule": "dependency_validation",
                    "field": "dependencies",
                    "message": "One or more dependencies are missing",
                }
            )

        if draft.get("require_knowledge") and not knowledge_topics:
            errors.append(
                {
                    "rule": "knowledge_validation",
                    "field": "knowledge",
                    "message": "Knowledge topics are required for this builder",
                }
            )
            suggestions.append("Attach at least one knowledge topic.")

        if draft.get("requires_concierge") and not relationships.get("concierge_id"):
            errors.append(
                {
                    "rule": "relationship_validation",
                    "field": "concierge",
                    "message": "Concierge relationship is required",
                }
            )
            suggestions.append("Attach or create a Concierge before finishing.")

        live = {
            "has_errors": bool(errors),
            "error_count": len(errors),
            "suggestion_count": len(suggestions),
        }
        return {
            "ok": not errors,
            "errors": errors,
            "suggestions": suggestions,
            "live": live,
            "rules_checked": list(self.rule_ids),
        }

    def status(self) -> dict[str, Any]:
        return {"ready": True, "rules": list(VALIDATION_RULES)}
