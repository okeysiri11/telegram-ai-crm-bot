# Prompt service — templates, variables, versioning, validation, inheritance.

from __future__ import annotations

import re
from typing import Any

from platform_ai.exceptions import AIPromptValidationError
from platform_ai.models import PromptTemplate
from platform_ai.prompt_templates import BUILTIN_TEMPLATES

_VAR_PATTERN = re.compile(r"\{\{(\w+)\}\}")


class PromptService:
    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}

    def reset(self) -> None:
        self._templates.clear()

    def load_defaults(self) -> int:
        for tpl in BUILTIN_TEMPLATES:
            self.register(tpl)
        return len(BUILTIN_TEMPLATES)

    def register(self, template: PromptTemplate) -> None:
        key = f"{template.template_id}:v{template.version}"
        self._templates[key] = template
        self._templates[template.template_id] = template

    def get(self, template_id: str, version: int | None = None) -> PromptTemplate:
        if version is not None:
            key = f"{template_id}:v{version}"
            if key in self._templates:
                return self._templates[key]
        if template_id not in self._templates:
            raise AIPromptValidationError(f"Template not found: {template_id}")
        return self._templates[template_id]

    def list_templates(self) -> list[PromptTemplate]:
        seen: set[str] = set()
        result: list[PromptTemplate] = []
        for tpl in self._templates.values():
            if tpl.template_id in seen:
                continue
            seen.add(tpl.template_id)
            result.append(tpl)
        return result

    def extract_variables(self, body: str) -> list[str]:
        return list(dict.fromkeys(_VAR_PATTERN.findall(body)))

    def validate_variables(self, template: PromptTemplate, variables: dict[str, Any]) -> None:
        required = template.variables or self.extract_variables(template.body)
        missing = [v for v in required if v not in variables]
        if missing:
            raise AIPromptValidationError(f"Missing template variables: {', '.join(missing)}")

    def render(self, template_id: str, variables: dict[str, Any], *, version: int | None = None) -> str:
        template = self.get(template_id, version)
        body = template.body

        if template.parent_id:
            parent = self.get(template.parent_id)
            parent_rendered = self._render_body(parent.body, variables)
            variables = {**variables, "_parent": parent_rendered}
            body = f"{parent_rendered}\n\n{body}"

        self.validate_variables(template, variables)
        return self._render_body(body, variables)

    def _render_body(self, body: str, variables: dict[str, Any]) -> str:
        def replacer(match: re.Match[str]) -> str:
            key = match.group(1)
            if key not in variables:
                raise AIPromptValidationError(f"Missing variable: {key}")
            return str(variables[key])

        return _VAR_PATTERN.sub(replacer, body)

    def create_version(self, template_id: str, body: str, *, description: str = "") -> PromptTemplate:
        current = self.get(template_id)
        new_version = current.version + 1
        variables = self.extract_variables(body)
        template = PromptTemplate(
            template_id=template_id,
            name=current.name,
            body=body,
            version=new_version,
            parent_id=current.parent_id,
            variables=variables,
            description=description or current.description,
        )
        self.register(template)
        return template


prompt_service = PromptService()
