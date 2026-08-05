"""Context sources — collectors for enterprise context layers."""

from __future__ import annotations

import time
from typing import Any, Callable

from platform_memory.runtime_models import (
    ContextFragment,
    ContextSourceType,
    SensitivityLevel,
    Visibility,
    new_id,
)

Collector = Callable[[dict[str, Any]], list[ContextFragment]]


class ContextSourceRegistry:
    def __init__(self) -> None:
        self._collectors: dict[str, Collector] = {}
        self._store: dict[str, list[ContextFragment]] = {}
        self._seeded = False

    def reset(self) -> None:
        self._collectors.clear()
        self._store.clear()
        self._seeded = False

    def register(self, source: str, collector: Collector) -> None:
        self._collectors[source] = collector

    def put(self, source: str, fragments: list[ContextFragment]) -> None:
        self._store.setdefault(source, []).extend(fragments)

    def ensure_seed(self) -> None:
        if self._seeded:
            return
        now = time.time()
        seeds: dict[str, list[ContextFragment]] = {
            ContextSourceType.USER_PROFILE.value: [
                ContextFragment(
                    fragment_id=new_id("cfr"),
                    source=ContextSourceType.USER_PROFILE,
                    key="role",
                    content="User role: enterprise owner; prefers concise answers.",
                    sensitivity=SensitivityLevel.INTERNAL,
                    visibility=Visibility.USER,
                    metadata={"user_id": "u_demo"},
                )
            ],
            ContextSourceType.ORGANIZATION.value: [
                ContextFragment(
                    fragment_id=new_id("cfr"),
                    source=ContextSourceType.ORGANIZATION,
                    key="org",
                    content="Organization: ADOS Enterprise; industry: AI OS platforms.",
                    sensitivity=SensitivityLevel.PUBLIC,
                    visibility=Visibility.TENANT,
                    metadata={"tenant_id": "t_demo"},
                )
            ],
            ContextSourceType.PROJECT.value: [
                ContextFragment(
                    fragment_id=new_id("cfr"),
                    source=ContextSourceType.PROJECT,
                    key="project",
                    content="Project: Sprint 36 Context Engine delivery.",
                    sensitivity=SensitivityLevel.INTERNAL,
                    visibility=Visibility.WORKSPACE,
                    metadata={"project_id": "p_demo"},
                )
            ],
            ContextSourceType.WORKSPACE.value: [
                ContextFragment(
                    fragment_id=new_id("cfr"),
                    source=ContextSourceType.WORKSPACE,
                    key="workspace",
                    content="Workspace: platform-builder; locale=en.",
                    sensitivity=SensitivityLevel.INTERNAL,
                    visibility=Visibility.WORKSPACE,
                    metadata={"workspace_id": "ws_demo"},
                )
            ],
            ContextSourceType.DOCUMENTS.value: [
                ContextFragment(
                    fragment_id=new_id("cfr"),
                    source=ContextSourceType.DOCUMENTS,
                    key="doc",
                    content="Document excerpt: CONTEXT_ENGINE architecture notes.",
                    sensitivity=SensitivityLevel.INTERNAL,
                    visibility=Visibility.WORKSPACE,
                )
            ],
            ContextSourceType.KNOWLEDGE_BASE.value: [
                ContextFragment(
                    fragment_id=new_id("cfr"),
                    source=ContextSourceType.KNOWLEDGE_BASE,
                    key="kb",
                    content="Knowledge: Context assembly priority is task→project→workspace→enterprise.",
                    sensitivity=SensitivityLevel.PUBLIC,
                    visibility=Visibility.GLOBAL,
                )
            ],
            ContextSourceType.WORKFLOW_STATE.value: [
                ContextFragment(
                    fragment_id=new_id("cfr"),
                    source=ContextSourceType.WORKFLOW_STATE,
                    key="wf",
                    content="Workflow state: approval_pipeline=running; amount=1000.",
                    sensitivity=SensitivityLevel.INTERNAL,
                    visibility=Visibility.SESSION,
                    metadata={"workflow_id": "wf_approval_pipeline"},
                )
            ],
            ContextSourceType.CONVERSATION_HISTORY.value: [
                ContextFragment(
                    fragment_id=new_id("cfr"),
                    source=ContextSourceType.CONVERSATION_HISTORY,
                    key="chat",
                    content="user: Need enterprise context for AI runtime.\nassistant: Assembling sources.",
                    sensitivity=SensitivityLevel.INTERNAL,
                    visibility=Visibility.SESSION,
                )
            ],
            ContextSourceType.AGENT_MEMORY.value: [
                ContextFragment(
                    fragment_id=new_id("cfr"),
                    source=ContextSourceType.AGENT_MEMORY,
                    key="agent",
                    content="Agent memory: prefer platform_memory ContextAssembler over duplicates.",
                    sensitivity=SensitivityLevel.INTERNAL,
                    visibility=Visibility.TENANT,
                    metadata={"agent_id": "agent_orchestrator"},
                )
            ],
            ContextSourceType.RUNTIME_VARIABLES.value: [
                ContextFragment(
                    fragment_id=new_id("cfr"),
                    source=ContextSourceType.RUNTIME_VARIABLES,
                    key="vars",
                    content="runtime.vars: {mode=sync, budget_tokens=2048}",
                    sensitivity=SensitivityLevel.INTERNAL,
                    visibility=Visibility.SESSION,
                    expires_at=now + 3600,
                )
            ],
        }
        for source, frags in seeds.items():
            self._store[source] = frags
            self.register(source, self._make_store_collector(source))
        self._seeded = True

    def _make_store_collector(self, source: str) -> Collector:
        def _collect(query: dict[str, Any]) -> list[ContextFragment]:
            rows = list(self._store.get(source, []))
            # allow injecting extra from query.overrides
            extras = query.get("inject", {}).get(source) or []
            for item in extras:
                if isinstance(item, ContextFragment):
                    rows.append(item)
                elif isinstance(item, dict):
                    rows.append(
                        ContextFragment(
                            fragment_id=str(item.get("fragment_id") or new_id("cfr")),
                            source=source,
                            key=str(item.get("key") or "custom"),
                            content=str(item.get("content") or ""),
                            sensitivity=item.get("sensitivity") or SensitivityLevel.INTERNAL.value,
                            visibility=item.get("visibility") or Visibility.TENANT.value,
                            metadata=dict(item.get("metadata") or {}),
                            expires_at=item.get("expires_at"),
                            version=int(item.get("version") or 1),
                        )
                    )
            return rows

        return _collect

    def list_sources(self) -> list[dict[str, Any]]:
        self.ensure_seed()
        rows = []
        for source in ContextSourceType:
            frags = self._store.get(source.value, [])
            rows.append(
                {
                    "source": source.value,
                    "enabled": source.value in self._collectors,
                    "fragment_count": len(frags),
                    "rank": __import__("platform_memory.runtime_models", fromlist=["SOURCE_RANK"]).SOURCE_RANK.get(
                        source.value, 0
                    ),
                }
            )
        return rows

    def collect(
        self,
        *,
        sources: list[str] | None = None,
        query: dict[str, Any] | None = None,
    ) -> list[ContextFragment]:
        self.ensure_seed()
        query = query or {}
        wanted = sources or [s.value for s in ContextSourceType]
        out: list[ContextFragment] = []
        for source in wanted:
            collector = self._collectors.get(source)
            if collector is None:
                continue
            out.extend(collector(query))
        return out


source_registry = ContextSourceRegistry()
