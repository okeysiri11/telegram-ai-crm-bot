# Context engine — global, app, user, org, conversation, task context.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish

from ecosystem.assistant.events import ContextRestoredEvent
from ecosystem.assistant.models import ContextBundle
from ecosystem.shared.exceptions import NotFoundError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class ContextEngine:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    def get_or_create(self, user_id: str) -> ContextBundle:
        for bundle in self._store.context_bundles.list_all():
            if bundle.user_id == user_id:
                return bundle
        bundle = ContextBundle(user_id=user_id)
        self._store.context_bundles.save(bundle.context_id, bundle)
        return bundle

    def update(
        self,
        user_id: str,
        *,
        global_context: dict[str, Any] | None = None,
        application_context: dict[str, Any] | None = None,
        user_context: dict[str, Any] | None = None,
        organization_context: dict[str, Any] | None = None,
        conversation_context: dict[str, Any] | None = None,
        task_context: dict[str, Any] | None = None,
    ) -> ContextBundle:
        bundle = self.get_or_create(user_id)
        if global_context is not None:
            bundle.global_context.update(global_context)
        if application_context is not None:
            bundle.application_context.update(application_context)
        if user_context is not None:
            bundle.user_context.update(user_context)
        if organization_context is not None:
            bundle.organization_context.update(organization_context)
        if conversation_context is not None:
            bundle.conversation_context.update(conversation_context)
        if task_context is not None:
            bundle.task_context.update(task_context)
        bundle.updated_at = time.time()
        self._store.context_bundles.save(bundle.context_id, bundle)
        return bundle

    def assemble(self, user_id: str) -> dict[str, Any]:
        bundle = self.get_or_create(user_id)
        return {
            "user_id": user_id,
            "global": dict(bundle.global_context),
            "application": dict(bundle.application_context),
            "user": dict(bundle.user_context),
            "organization": dict(bundle.organization_context),
            "conversation": dict(bundle.conversation_context),
            "task": dict(bundle.task_context),
        }

    async def restore(self, user_id: str, conversation_id: str = "") -> ContextBundle:
        bundle = self.get_or_create(user_id)
        if conversation_id:
            conversation = self._store.conversations.get(conversation_id)
            if conversation and conversation.context_snapshot:
                bundle.conversation_context.update(conversation.context_snapshot)
                bundle.updated_at = time.time()
                self._store.context_bundles.save(bundle.context_id, bundle)
        await publish(
            ContextRestoredEvent(
                context_id=bundle.context_id,
                user_id=user_id,
                conversation_id=conversation_id,
            )
        )
        return bundle

    def get(self, user_id: str) -> ContextBundle:
        for bundle in self._store.context_bundles.list_all():
            if bundle.user_id == user_id:
                return bundle
        raise NotFoundError("ContextBundle", user_id)


context_engine = ContextEngine()
