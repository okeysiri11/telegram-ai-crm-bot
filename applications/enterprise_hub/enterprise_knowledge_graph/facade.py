"""Enterprise Knowledge Graph Suite — Sprint 24.2 / v7.2.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_enterprise_knowledge_graph.facade import EnterpriseKnowledgeGraphLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EnterpriseKnowledgeGraphSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = EnterpriseKnowledgeGraphLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = EnterpriseKnowledgeGraphLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("ekg_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.ekg_bootstraps.save(bid, record)
        for e in full["entities"]:
            self.store.ekg_entities.save(e["entity_id"], {**e, "created_at": _now()})
        for i, edge in enumerate(full["edges"]):
            eid = _id("ekg_edge")
            self.store.ekg_edges.save(eid, {"edge_id": eid, **edge, "created_at": _now()})
        cid = _id("ekg_ctx")
        self.store.ekg_contexts.save(cid, {"context_id": cid, **full["context"], "created_at": _now()})
        sid = _id("ekg_search")
        self.store.ekg_searches.save(sid, {"search_id": sid, **full["search"], "created_at": _now()})
        tid = _id("ekg_tl")
        self.store.ekg_timelines.save(tid, {"timeline_id": tid, **full["timeline"], "created_at": _now()})
        self.store.ekg_bootstraps.save(bid, record)
        return record

    def upsert_entity(self, **kwargs: Any) -> dict[str, Any]:
        try:
            entity = self.library.graph.upsert(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.ekg_entities.save(entity["entity_id"], {**entity, "updated_at": _now()})
        self.library.timeline.append(entity_id=entity["entity_id"], event_type="created", summary="upsert")
        return entity

    def link(self, **kwargs: Any) -> dict[str, Any]:
        try:
            edge = self.library.relations.link(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        eid = _id("ekg_edge")
        record = {"edge_id": eid, **edge, "created_at": _now()}
        self.store.ekg_edges.save(eid, record)
        return record

    def remember(self, **kwargs: Any) -> dict[str, Any]:
        try:
            item = self.library.memory.record(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        mid = _id("ekg_mem")
        record = {"memory_id": mid, **item, "created_at": _now()}
        self.store.ekg_memory.save(mid, record)
        return record

    def build_context(self, **kwargs: Any) -> dict[str, Any]:
        # enrich from live modules when available (no duplicated logic)
        sources = list(kwargs.get("sources") or [])
        try:
            from applications.enterprise_hub import enterprise_hub

            if not sources:
                sources = None
            related = list(kwargs.get("related") or [])
            for eid in kwargs.get("entity_ids") or []:
                related.extend(self.library.relations.neighbors(eid))
            kwargs = {**kwargs, "related": related, "sources": sources}
        except Exception:
            pass
        try:
            ctx = self.library.context.build(**{k: v for k, v in kwargs.items() if k in ("task", "entity_ids", "sources", "related", "memory", "elapsed_ms") and v is not None})
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        entities = []
        for eid in kwargs.get("entity_ids") or []:
            e = self.store.ekg_entities.get(eid) or self.library.graph.get(eid)
            if e:
                entities.append(e)
        ai_ctx = self.library.ai_context.build(
            context=ctx,
            entities=entities,
            decisions=[m for m in self.store.ekg_memory.list_all() if m.get("kind") == "decision"],
            recommendations=kwargs.get("recommendations"),
            outcomes=kwargs.get("outcomes"),
        )
        cid = _id("ekg_ctx")
        record = {"context_id": cid, **ctx, "ai_context": ai_ctx, "created_at": _now()}
        self.store.ekg_contexts.save(cid, record)
        return record

    def semantic_search(self, *, text: str) -> dict[str, Any]:
        entities = self.store.ekg_entities.list_all() or self.library.graph.list_entities()
        edges = self.store.ekg_edges.list_all() or self.library.relations.all_edges()
        try:
            result = self.library.search.query(text=text, entities=entities, edges=edges)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        sid = _id("ekg_search")
        record = {"search_id": sid, **result, "created_at": _now()}
        self.store.ekg_searches.save(sid, record)
        return record

    def timeline(self, *, entity_id: str) -> dict[str, Any]:
        # merge library timeline with store markers
        tl = self.library.timeline.for_entity(entity_id)
        if not tl["events"]:
            entity = self.store.ekg_entities.get(entity_id)
            if not entity:
                raise NotFoundError(f"entity not found: {entity_id}")
            tl = {
                "entity_id": entity_id,
                "events": [{"event_type": "created", "summary": "from_store"}],
                "created": [{"event_type": "created"}],
                "changes": [],
                "processes": [],
                "documents": [],
                "ai_recommendations": [],
                "owner_approvals": [],
            }
        tid = _id("ekg_tl")
        record = {"timeline_id": tid, **tl, "created_at": _now()}
        self.store.ekg_timelines.save(tid, record)
        return record

    def learn(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.learning.apply_confirmed(**kwargs)
        if result.get("learned") and result.get("strengthen"):
            s = result["strengthen"]
            try:
                self.library.relations.strengthen(
                    source_id=s["source_id"],
                    relation=s["relation"],
                    target_id=s["target_id"],
                )
            except ValueError:
                pass
        for eid in result.get("archive_entity_ids") or []:
            try:
                self.library.graph.set_flags(eid, archived=True)
                if self.store.ekg_entities.get(eid):
                    e = self.store.ekg_entities.get(eid)
                    e["archived"] = True
                    self.store.ekg_entities.save(eid, e)
            except ValueError:
                pass
        lid = _id("ekg_learn")
        record = {"learning_id": lid, **result, "created_at": _now()}
        self.store.ekg_learning.save(lid, record)
        return record

    def owner_control(self, **kwargs: Any) -> dict[str, Any]:
        try:
            result = self.library.owner.act(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        payload = kwargs.get("payload") or {}
        action = result["action"]
        eid = payload.get("entity_id")
        if eid and action == "confirm_knowledge":
            try:
                self.library.graph.set_flags(eid, confirmed=True)
            except ValueError:
                pass
            if self.store.ekg_entities.get(eid):
                e = dict(self.store.ekg_entities.get(eid))
                e["confirmed"] = True
                self.store.ekg_entities.save(eid, e)
        if eid and action == "archive_knowledge":
            try:
                self.library.graph.set_flags(eid, archived=True)
            except ValueError:
                pass
            if self.store.ekg_entities.get(eid):
                e = dict(self.store.ekg_entities.get(eid))
                e["archived"] = True
                self.store.ekg_entities.save(eid, e)
        if eid and action == "forbid_ai_use":
            try:
                self.library.graph.set_flags(eid, ai_allowed=False)
            except ValueError:
                pass
            if self.store.ekg_entities.get(eid):
                e = dict(self.store.ekg_entities.get(eid))
                e["ai_allowed"] = False
                self.store.ekg_entities.save(eid, e)
        oid = _id("ekg_own")
        record = {"owner_id": oid, **result, "created_at": _now()}
        self.store.ekg_owner.save(oid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.ekg_bootstraps.list_all()),
            "entities": len(self.store.ekg_entities.list_all()),
            "edges": len(self.store.ekg_edges.list_all()),
            "central_context_source": True,
        }


enterprise_knowledge_graph = EnterpriseKnowledgeGraphSuite()
