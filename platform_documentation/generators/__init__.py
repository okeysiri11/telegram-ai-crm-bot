"""Documentation generators — Sprint 21.6."""

from __future__ import annotations

from typing import Any

from platform_documentation.models import HUB_MODULES
from platform_documentation.templates import TemplateCatalog


class ArchitectureGenerator:
    def generate(self) -> dict[str, Any]:
        layers = ["presentation", "application", "domain", "infrastructure", "platform_shared"]
        return {
            "kind": "architecture",
            "title": "Enterprise AI Platform Architecture",
            "layers": layers,
            "modules": list(HUB_MODULES),
            "dependencies": [
                {"from": "command_center", "to": "digital_twin"},
                {"from": "process_mining", "to": "event_platform"},
                {"from": "quality_assurance", "to": "api_standardization"},
                {"from": "security_hardening", "to": "enterprise_hub"},
            ],
            "diagrams": ["component", "sequence", "deployment"],
        }


class ModuleGenerator:
    def __init__(self) -> None:
        self.templates = TemplateCatalog()

    def generate(self, module: str | None = None) -> list[dict[str, Any]]:
        targets = [module] if module else list(HUB_MODULES)
        docs = []
        for name in targets:
            if name not in HUB_MODULES:
                raise ValueError(f"unknown module: {name}")
            page = self.templates.render(category="modules", title=f"{name} module")
            docs.append(
                {
                    **page,
                    "module": name,
                    "purpose": f"Enterprise Hub {name} capability",
                    "public_services": [f"{name}.facade", f"{name}.api"],
                    "configuration": f"{name}_api_prefix",
                    "extension_points": ["hooks", "plugins"],
                    "usage_example": f"enterprise_hub.{name}.bootstrap()",
                }
            )
        return docs


class ApiDocGenerator:
    def generate(self) -> dict[str, Any]:
        return {
            "kind": "api",
            "openapi": "3.1.0",
            "swagger": True,
            "redoc": True,
            "endpoints": [
                {"path": "/api/enterprise-hub/v1/health", "method": "GET"},
                {"path": "/api/enterprise-eqa/v1/bootstrap", "method": "POST"},
                {"path": "/api/enterprise-edo/v1/docs", "method": "GET"},
            ],
            "examples": {
                "request": {"method": "GET", "path": "/health"},
                "response": {"status": "ok"},
                "errors": [{"code": 400, "message": "validation_error"}],
            },
            "versions": ["v1", "v2"],
        }


class SdkDocGenerator:
    def generate(self) -> dict[str, Any]:
        return {
            "kind": "sdk",
            "languages": ["python", "typescript"],
            "packages": ["enterprise_sdk", "cursor-sdk"],
            "quickstart": "pip install enterprise-sdk && from enterprise_sdk import Client",
            "examples": ["auth", "list_modules", "invoke_workflow"],
        }


class AiDocGenerator:
    def generate(self) -> dict[str, Any]:
        return {
            "kind": "ai",
            "components": [
                "ai_orchestrator",
                "ai_agents",
                "prompt_registry",
                "tool_registry",
                "knowledge_platform",
                "memory_engine",
            ],
            "task_routes": ["plan", "delegate", "aggregate", "recover"],
        }


class DeploymentDocGenerator:
    def generate(self) -> dict[str, Any]:
        return {
            "kind": "deployment",
            "topics": ["docker", "kubernetes", "helm", "ci_cd", "migrations", "backup", "restore"],
            "manifests": ["Deployment", "Service", "Ingress", "ConfigMap"],
        }


class AdministrationDocGenerator:
    def generate(self) -> dict[str, Any]:
        return {
            "kind": "administration",
            "guides": ["tenancy", "rbac", "secrets", "observability", "incident_response"],
        }


class UserGuideGenerator:
    def generate(self) -> dict[str, Any]:
        return {
            "kind": "user_guides",
            "guides": ["getting_started", "command_center", "workflows", "ai_assistant"],
        }
