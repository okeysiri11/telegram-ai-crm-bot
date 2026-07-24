"""AI Provider Hub Suite — Sprint 24.9 / v7.9.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_enterprise_ai_provider_hub.facade import AIProviderHubLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIProviderHubSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = AIProviderHubLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = AIProviderHubLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("aph_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.aph_bootstraps.save(bid, record)
        for p in full["providers"]:
            self.store.aph_providers.save(p["provider_id"], {**p, "created_at": _now()})
        for m in full["models"]:
            self.store.aph_models.save(m["model_id"], {**m, "created_at": _now()})
        for key, attr, prefix in (
            ("route", "aph_routes", "aph_rte"),
            ("fallback", "aph_fallbacks", "aph_fb"),
            ("prompt", "aph_prompts", "aph_prm"),
            ("cost", "aph_costs", "aph_cost"),
            ("analytics", "aph_analytics", "aph_an"),
            ("security", "aph_security", "aph_sec"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        self.store.aph_bootstraps.save(bid, record)
        return record

    def register_provider(self, **kwargs: Any) -> dict[str, Any]:
        try:
            provider = self.library.providers.register(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.aph_providers.save(provider["provider_id"], {**provider, "created_at": _now()})
        return provider

    def register_model(self, **kwargs: Any) -> dict[str, Any]:
        try:
            model = self.library.models.register(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.aph_models.save(model["model_id"], {**model, "created_at": _now()})
        return model

    def list_providers(self) -> dict[str, Any]:
        items = self.store.aph_providers.list_all()
        return {"providers": items, "count": len(items), "extensible": True}

    def list_models(self) -> dict[str, Any]:
        items = self.store.aph_models.list_all()
        return {"models": items, "count": len(items)}

    def route(self, *, task_type: str, prefer_cost: bool = False, prefer_speed: bool = False, prefer_quality: bool = True, require_local: bool = False, security_tier: str = "standard") -> dict[str, Any]:
        models = self.store.aph_models.list_all()
        if not models:
            raise ValidationError("no models registered")
        try:
            result = self.library.router.route(
                task_type=task_type,
                models=models,
                prefer_cost=prefer_cost,
                prefer_speed=prefer_speed,
                prefer_quality=prefer_quality,
                require_local=require_local,
                security_tier=security_tier,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("aph_rte")
        record = {"route_id": rid, **result, "created_at": _now()}
        self.store.aph_routes.save(rid, record)
        return record

    def fallback(self, *, chain: list[dict[str, Any]] | None = None, fail_until: int = 0) -> dict[str, Any]:
        try:
            result = self.library.fallback.execute(chain=chain or [], fail_until=fail_until)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("aph_fb")
        record = {"fallback_id": rid, **result, "created_at": _now()}
        self.store.aph_fallbacks.save(rid, record)
        return record

    def assemble_prompt(self, **kwargs: Any) -> dict[str, Any]:
        try:
            # light EKG hook
            try:
                from applications.enterprise_hub import enterprise_hub

                if hasattr(enterprise_hub, "enterprise_knowledge_graph"):
                    refs = list(kwargs.get("knowledge_graph_refs") or [])
                    if not refs:
                        kwargs["knowledge_graph_refs"] = ["ekg:available"]
            except Exception:
                pass
            result = self.library.prompt.assemble(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("aph_prm")
        record = {"prompt_id": rid, **result, "created_at": _now()}
        self.store.aph_prompts.save(rid, record)
        return record

    def track_cost(self, *, entries: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        result = self.library.cost.track(entries=entries)
        rid = _id("aph_cost")
        record = {"cost_id": rid, **result, "created_at": _now()}
        self.store.aph_costs.save(rid, record)
        return record

    def usage_analytics(self, *, requests: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        result = self.library.analytics.summarize(requests=requests)
        rid = _id("aph_an")
        record = {"analytics_id": rid, **result, "created_at": _now()}
        self.store.aph_analytics.save(rid, record)
        return record

    def secure(self, **kwargs: Any) -> dict[str, Any]:
        try:
            result = self.library.security.protect(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("aph_sec")
        record = {"security_id": rid, **result, "created_at": _now()}
        self.store.aph_security.save(rid, record)
        return record

    def invoke(self, *, task_type: str = "general_chat", user_prompt: str = "", prefer_quality: bool = True) -> dict[str, Any]:
        """Unified hub invoke — modules call this instead of providers."""
        route = self.route(task_type=task_type, prefer_quality=prefer_quality)
        prompt = self.assemble_prompt(template="enterprise_default", user_prompt=user_prompt or "ping")
        # simulate success via selected provider; no outbound network
        usage = {
            "success": True,
            "latency_ms": 100,
            "cost": 0.01,
            "quality": 0.8,
            "fallback_used": False,
            "model_id": route["selected_model"],
            "provider_id": route["selected_provider"],
        }
        self.track_cost(entries=[{
            "provider_id": route["selected_provider"],
            "client_id": "hub",
            "agent_id": "router",
            "unit": "platform",
            "task_type": task_type,
            "cost": 0.01,
        }])
        self.usage_analytics(requests=[usage])
        rid = _id("aph_inv")
        record = {
            "invoke_id": rid,
            "route": route,
            "prompt": {"prompt_id": prompt["prompt_id"], "gateway": True},
            "result": usage,
            "direct_provider_call": False,
            "via_hub_only": True,
            "created_at": _now(),
        }
        self.store.aph_invokes.save(rid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.aph_bootstraps.list_all()),
            "providers": len(self.store.aph_providers.list_all()),
            "models": len(self.store.aph_models.list_all()),
            "via_hub_only": True,
        }


ai_provider_hub = AIProviderHubSuite()
