"""Documentation Platform Suite facade — Sprint 21.6 / v6.0.0-rc6."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_documentation.facade import DocumentationLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DocumentationPlatformSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = DocumentationLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations()

    def bootstrap(self) -> dict[str, Any]:
        self.library = DocumentationLibrary()
        version = DEFAULT_CONFIG.application_version
        result = self.library.bootstrap(version=version)
        bid = _id("edo_boot")
        dash = result.pop("dashboard")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": version,
            "bootstrapped_at": _now(),
        }
        self.store.edo_bootstraps.save(bid, record)
        for doc in self.library.registry.list_all():
            self.store.edo_docs.save(doc["doc_id"], doc)
        dash_id = _id("edo_dash")
        self.store.edo_dashboards.save(dash_id, {"dashboard_id": dash_id, **dash, "rendered_at": _now()})
        pub_id = result["publish_id"]
        self.store.edo_publications.save(
            pub_id,
            {
                "publish_id": pub_id,
                "formats": result["published_formats"],
                "developer_portal": result["developer_portal"],
                "published_at": _now(),
            },
        )
        record["dashboard_id"] = dash_id
        self.store.edo_bootstraps.save(bid, record)
        return record

    def register_doc(self, **kwargs: Any) -> dict[str, Any]:
        try:
            doc = self.library.registry.register(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.edo_docs.save(doc["doc_id"], doc)
        self.library.search.index([doc])
        return doc

    def search(self, **kwargs: Any) -> dict[str, Any]:
        # ensure index has store docs
        if not self.library.search._index:
            self.library.search.index(self.store.edo_docs.list_all())
        result = self.library.search.search(**kwargs)
        sid = _id("edo_search")
        record = {"search_id": sid, **result, "searched_at": _now()}
        self.store.edo_searches.save(sid, record)
        return record

    def publish(self, formats: list[str] | None = None) -> dict[str, Any]:
        docs = self.store.edo_docs.list_all() or self.library.registry.list_all()
        try:
            result = self.library.publishing.publish(docs=docs, formats=formats)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.edo_publications.save(result["publish_id"], {**result, "published_at": _now()})
        return result

    def quality(self) -> dict[str, Any]:
        docs = self.store.edo_docs.list_all() or self.library.registry.list_all()
        result = self.library.quality.validate(docs)
        qid = _id("edo_qual")
        record = {"quality_id": qid, **result, "validated_at": _now()}
        self.store.edo_quality.save(qid, record)
        return record

    def generate(self, kind: str) -> dict[str, Any]:
        generators = {
            "architecture": self.library.architecture.generate,
            "api": self.library.api.generate,
            "sdk": self.library.sdk.generate,
            "ai": self.library.ai.generate,
            "deployment": self.library.deployment.generate,
            "modules": lambda: {"modules": self.library.modules.generate()},
        }
        if kind not in generators:
            raise ValidationError(f"unknown generator: {kind}")
        payload = generators[kind]()
        gid = _id("edo_gen")
        record = {"generation_id": gid, "kind": kind, "payload": payload, "generated_at": _now()}
        self.store.edo_generations.save(gid, record)
        return record

    def dashboard(self) -> dict[str, Any]:
        items = self.store.edo_dashboards.list_all()
        if not items:
            raise NotFoundError("documentation dashboard not found; bootstrap first")
        return items[-1]

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.edo_bootstraps.list_all()),
            "docs": len(self.store.edo_docs.list_all()),
            "publications": len(self.store.edo_publications.list_all()),
            "dashboards": len(self.store.edo_dashboards.list_all()),
        }


documentation_platform = DocumentationPlatformSuite()
