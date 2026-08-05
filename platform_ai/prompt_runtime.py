"""Prompt Runtime façade — templates, versioning, validation, cache. Sprint 36.3."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from platform_ai.exceptions import AIPromptValidationError
from platform_ai.models import PromptTemplate
from platform_ai.prompt_service import prompt_service
from platform_ai.runtime_models import PromptVersionRecord, new_id


class PromptCache:
    def __init__(self, *, max_entries: int = 256) -> None:
        self._store: dict[str, tuple[float, str]] = {}
        self._max = max_entries
        self.hits = 0
        self.misses = 0

    def reset(self) -> None:
        self._store.clear()
        self.hits = 0
        self.misses = 0

    def _key(self, template_id: str, version: int | None, variables: dict[str, Any]) -> str:
        raw = f"{template_id}|{version}|{sorted(variables.items())}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, template_id: str, version: int | None, variables: dict[str, Any]) -> str | None:
        key = self._key(template_id, version, variables)
        hit = self._store.get(key)
        if hit is None:
            self.misses += 1
            return None
        self.hits += 1
        return hit[1]

    def set(self, template_id: str, version: int | None, variables: dict[str, Any], value: str) -> None:
        key = self._key(template_id, version, variables)
        self._store[key] = (time.time(), value)
        if len(self._store) > self._max:
            oldest = sorted(self._store.items(), key=lambda x: x[1][0])[: len(self._store) - self._max]
            for k, _ in oldest:
                self._store.pop(k, None)


class PromptRuntime:
    """System/user prompts, templates, variables, versioning, validation, cache."""

    def __init__(self) -> None:
        self.cache = PromptCache()
        self._versions: dict[str, list[PromptVersionRecord]] = {}
        self._system_prompts: dict[str, str] = {
            "default": "You are ADOS Enterprise AI. Be precise, auditable, and helpful.",
            "coder": "You are an enterprise coding assistant. Prefer existing modules.",
            "analyst": "You are an enterprise analyst. Ground answers in platform facts.",
        }

    def reset(self) -> None:
        self.cache.reset()
        self._versions.clear()
        prompt_service.reset()

    def ensure_defaults(self) -> None:
        if not prompt_service.list_templates():
            prompt_service.load_defaults()

    def list_system_prompts(self) -> dict[str, str]:
        return dict(self._system_prompts)

    def set_system_prompt(self, key: str, body: str) -> dict[str, str]:
        self._system_prompts[key] = body
        return {key: body}

    def list_templates(self) -> list[dict[str, Any]]:
        self.ensure_defaults()
        return [t.to_dict() for t in prompt_service.list_templates()]

    def get_template(self, template_id: str, version: int | None = None) -> dict[str, Any]:
        self.ensure_defaults()
        return prompt_service.get(template_id, version).to_dict()

    def create_template(
        self,
        *,
        template_id: str | None = None,
        name: str,
        body: str,
        system_prompt: str = "",
        description: str = "",
        parent_id: str | None = None,
    ) -> dict[str, Any]:
        tid = template_id or new_id("ptpl")
        variables = prompt_service.extract_variables(body)
        if system_prompt:
            variables = list(dict.fromkeys(variables + prompt_service.extract_variables(system_prompt)))
        tpl = PromptTemplate(
            template_id=tid,
            name=name,
            body=body if not system_prompt else f"{system_prompt}\n\n{body}",
            version=1,
            parent_id=parent_id,
            variables=variables,
            description=description,
        )
        prompt_service.register(tpl)
        self._record_version(tid, 1, body, system_prompt=system_prompt, variables=variables, changelog="initial")
        return tpl.to_dict()

    def create_version(
        self,
        template_id: str,
        body: str,
        *,
        system_prompt: str = "",
        changelog: str = "",
    ) -> dict[str, Any]:
        self.ensure_defaults()
        full = f"{system_prompt}\n\n{body}" if system_prompt else body
        tpl = prompt_service.create_version(template_id, full, description=changelog)
        self._record_version(
            template_id,
            tpl.version,
            body,
            system_prompt=system_prompt,
            variables=tpl.variables,
            changelog=changelog,
        )
        self.cache.reset()
        return tpl.to_dict()

    def _record_version(
        self,
        template_id: str,
        version: int,
        body: str,
        *,
        system_prompt: str = "",
        variables: list[str] | None = None,
        changelog: str = "",
    ) -> PromptVersionRecord:
        for prev in self._versions.get(template_id, []):
            prev.is_active = False
        rec = PromptVersionRecord(
            template_id=template_id,
            version=version,
            body=body,
            system_prompt=system_prompt,
            variables=list(variables or []),
            changelog=changelog,
            is_active=True,
        )
        self._versions.setdefault(template_id, []).append(rec)
        return rec

    def versions(self, template_id: str) -> list[dict[str, Any]]:
        self.ensure_defaults()
        rows = self._versions.get(template_id)
        if rows:
            return [r.to_dict() for r in rows]
        tpl = prompt_service.get(template_id)
        return [
            PromptVersionRecord(
                template_id=template_id,
                version=tpl.version,
                body=tpl.body,
                variables=list(tpl.variables),
                changelog="registered",
            ).to_dict()
        ]

    def validate(self, template_id: str, variables: dict[str, Any], *, version: int | None = None) -> dict[str, Any]:
        self.ensure_defaults()
        tpl = prompt_service.get(template_id, version)
        try:
            prompt_service.validate_variables(tpl, variables)
            return {"valid": True, "template_id": template_id, "variables": tpl.variables}
        except AIPromptValidationError as exc:
            return {"valid": False, "template_id": template_id, "error": str(exc), "variables": tpl.variables}

    def render(
        self,
        template_id: str,
        variables: dict[str, Any] | None = None,
        *,
        version: int | None = None,
        use_cache: bool = True,
        system_prompt_key: str | None = None,
    ) -> dict[str, Any]:
        self.ensure_defaults()
        variables = dict(variables or {})
        if use_cache:
            cached = self.cache.get(template_id, version, variables)
            if cached is not None:
                return {
                    "template_id": template_id,
                    "version": version,
                    "rendered": cached,
                    "cached": True,
                    "cache_hits": self.cache.hits,
                }
        rendered = prompt_service.render(template_id, variables, version=version)
        if system_prompt_key and system_prompt_key in self._system_prompts:
            rendered = f"{self._system_prompts[system_prompt_key]}\n\n{rendered}"
        if use_cache:
            self.cache.set(template_id, version, variables, rendered)
        return {
            "template_id": template_id,
            "version": version,
            "rendered": rendered,
            "cached": False,
            "cache_hits": self.cache.hits,
            "cache_misses": self.cache.misses,
        }

    def cache_stats(self) -> dict[str, Any]:
        return {"hits": self.cache.hits, "misses": self.cache.misses, "size": len(self.cache._store)}


prompt_runtime = PromptRuntime()
