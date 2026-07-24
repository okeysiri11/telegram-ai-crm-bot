"""Documentation library facade — Sprint 21.6."""

from __future__ import annotations

from typing import Any

from platform_documentation.administration import AdministrationDocGenerator
from platform_documentation.ai import AiDocGenerator
from platform_documentation.api import ApiDocGenerator
from platform_documentation.architecture import ArchitectureGenerator
from platform_documentation.changelog import Changelog
from platform_documentation.dashboard import DocumentationDashboard
from platform_documentation.deployment import DeploymentDocGenerator
from platform_documentation.diagrams import DiagramCatalog
from platform_documentation.generators import ModuleGenerator
from platform_documentation.models import DOC_CATEGORIES, INTEGRATION_TARGETS
from platform_documentation.publishing import PublishingEngine
from platform_documentation.quality import DocumentationQuality
from platform_documentation.registry import DocumentationRegistry
from platform_documentation.sdk import SdkDocGenerator
from platform_documentation.search import DocumentationSearch
from platform_documentation.templates import TemplateCatalog
from platform_documentation.user_guides import UserGuideGenerator
from platform_documentation.versioning import DocumentationVersioning


class DocumentationLibrary:
    def __init__(self) -> None:
        self.registry = DocumentationRegistry()
        self.templates = TemplateCatalog()
        self.architecture = ArchitectureGenerator()
        self.modules = ModuleGenerator()
        self.api = ApiDocGenerator()
        self.sdk = SdkDocGenerator()
        self.ai = AiDocGenerator()
        self.deployment = DeploymentDocGenerator()
        self.administration = AdministrationDocGenerator()
        self.user_guides = UserGuideGenerator()
        self.diagrams = DiagramCatalog()
        self.changelog = Changelog()
        self.search = DocumentationSearch()
        self.versioning = DocumentationVersioning()
        self.quality = DocumentationQuality()
        self.publishing = PublishingEngine()
        self.dashboard = DocumentationDashboard()

    def integrations(self) -> dict[str, Any]:
        return {"targets": list(INTEGRATION_TARGETS), "linked": True}

    def bootstrap(self, *, version: str = "6.0.0-rc6") -> dict[str, Any]:
        self.__init__()
        pages: list[dict[str, Any]] = []

        arch = self.architecture.generate()
        pages.append(
            self.registry.register(
                title=arch["title"],
                category="architecture",
                content=str(arch),
                version=version,
                kind="architecture",
                metadata=arch,
            )
        )

        for mod in self.modules.generate():
            pages.append(
                self.registry.register(
                    title=mod["title"],
                    category="modules",
                    content=mod.get("body", ""),
                    version=version,
                    module=mod["module"],
                    kind="module",
                    metadata=mod,
                )
            )

        for category, payload in (
            ("api", self.api.generate()),
            ("sdk", self.sdk.generate()),
            ("ai", self.ai.generate()),
            ("deployment", self.deployment.generate()),
            ("operations", self.administration.generate()),
            ("user_guides", self.user_guides.generate()),
            ("security", {"kind": "security", "topics": ["hardening", "zero_trust", "audit"]}),
        ):
            pages.append(
                self.registry.register(
                    title=f"{category.replace('_', ' ').title()} Documentation",
                    category=category if category in DOC_CATEGORIES else "operations",
                    content=str(payload),
                    version=version,
                    kind=payload.get("kind", category),
                    metadata=payload,
                )
            )

        for diag in self.diagrams.list_all():
            pages.append(
                self.registry.register(
                    title=diag["title"],
                    category="architecture",
                    content=str(diag),
                    version=version,
                    kind="diagram",
                    metadata=diag,
                )
            )

        for entry in self.changelog.entries(version=version):
            pages.append(
                self.registry.register(
                    title=entry["summary"],
                    category="architecture",
                    content=entry["summary"],
                    version=version,
                    kind="changelog",
                    metadata=entry,
                )
            )

        self.search.index(pages)
        quality = self.quality.validate(pages)
        published = self.publishing.publish(docs=pages)
        versions = self.versioning.matrix(version=version)
        dash = self.dashboard.render(
            registry_status=self.registry.status(),
            quality=quality,
            publish=published,
            version=version,
        )
        sample_search = self.search.search(query="architecture", category="architecture")
        return {
            "bootstrap": True,
            "docs_registered": len(pages),
            "categories": self.registry.by_category(),
            "templates": len(self.templates.list_all()),
            "modules_documented": len([p for p in pages if p.get("kind") == "module"]),
            "api_openapi": self.api.generate()["openapi"],
            "search_hits": sample_search["count"],
            "version_matrix": versions,
            "quality_passed": quality["passed"],
            "completeness": quality["completeness"],
            "publish_id": published["publish_id"],
            "published_formats": len(published["artifacts"]),
            "developer_portal": published["portals"]["developer"],
            "dashboard": dash,
            "integrations": self.integrations(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "registry": self.registry.status(),
            "categories": list(DOC_CATEGORIES),
            "search_index": len(self.search._index),
        }


documentation_library = DocumentationLibrary()
