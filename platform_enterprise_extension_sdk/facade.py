"""Extension SDK library facade — Sprint 25.0."""

from __future__ import annotations

from typing import Any

from platform_enterprise_extension_sdk.integrations import ExtensionIntegrations
from platform_enterprise_extension_sdk.lifecycle import ExtensionLifecycle
from platform_enterprise_extension_sdk.loader import ExtensionLoader
from platform_enterprise_extension_sdk.marketplace import MarketplaceFoundation
from platform_enterprise_extension_sdk.models import PRINCIPLES
from platform_enterprise_extension_sdk.permissions import PermissionEngine
from platform_enterprise_extension_sdk.public_api import PublicExtensionAPI
from platform_enterprise_extension_sdk.registry import ExtensionRegistry
from platform_enterprise_extension_sdk.sdk import ExtensionSDK
from platform_enterprise_extension_sdk.verification import VerificationPipeline


class ExtensionSDKLibrary:
    def __init__(self) -> None:
        self.registry = ExtensionRegistry()
        self.sdk = ExtensionSDK()
        self.loader = ExtensionLoader()
        self.permissions = PermissionEngine()
        self.marketplace = MarketplaceFoundation()
        self.verification = VerificationPipeline()
        self.lifecycle = ExtensionLifecycle()
        self.public_api = PublicExtensionAPI()
        self.integrations = ExtensionIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        caps = self.sdk.capabilities()
        scaffold = self.sdk.scaffold(extension_type="ai_skill", name="Beauty Upsell Skill")
        ext = self.registry.register(
            extension_id="ext_beauty_upsell",
            name="Beauty Upsell Skill",
            version="1.0.0",
            author="bidex",
            publisher="bidex",
            industry="beauty",
            extension_type="ai_skill",
            required_permissions=["commerce", "ai", "marketing"],
            compatibility={"platform_min": "8.0.0"},
        )
        perm_req = self.permissions.request(extension_id=ext["extension_id"], scopes=ext["required_permissions"])
        perm = self.permissions.decide(
            extension_id=ext["extension_id"],
            actor="platform_owner",
            action="approve",
            scopes=ext["required_permissions"],
        )
        ext = self.lifecycle.transition(extension=ext, to_status="testing")
        verified = self.verification.run(extension=ext)
        ext = {**ext, "signature": verified["signature"], "signed": True}
        ext = self.lifecycle.transition(extension=ext, to_status="verified")
        listing = self.marketplace.list_extension(extension={**ext, "status": "verified"}, category="ai_skills")
        ext = self.lifecycle.transition(extension=ext, to_status="published")
        installed = self.loader.install(extension=ext)
        ext = self.lifecycle.transition(extension=ext, to_status="installed")
        api_ok = self.public_api.call(method="extensions.register", payload={"extension_id": ext["extension_id"]})
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "extension_sdk_ready": True,
            "marketplace_foundation_ready": True,
            "extension_permissions_ready": True,
            "extension_lifecycle_ready": True,
            "public_api_only": True,
            "direct_core_access": False,
            "modifies_enterprise_core": False,
            "signed": True,
            "duplicates_core_logic": False,
            "status": "ready",
            "integrations": links,
            "full": {
                "capabilities": caps,
                "scaffold": scaffold,
                "extension": ext,
                "permission_request": perm_req,
                "permission_decision": perm,
                "verification": verified,
                "listing": listing,
                "installed": installed,
                "public_api": api_ok,
                "marketplace": self.marketplace.catalog(),
                "lifecycle_path": self.lifecycle.path(),
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "registry",
                "sdk",
                "loader",
                "permissions",
                "marketplace",
                "verification",
                "lifecycle",
                "public_api",
            ],
            "principles": self.principles(),
            "public_api_only": True,
        }


extension_sdk_library = ExtensionSDKLibrary()
