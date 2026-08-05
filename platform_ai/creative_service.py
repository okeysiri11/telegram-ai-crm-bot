"""Creative Factory service façade — Sprint 36.9."""

from __future__ import annotations

from typing import Any

from platform_ai.creative_engine import CreativeFactoryEngine, creative_factory_engine
from platform_ai.creative_models import CreativeType, MediaModality, PublishChannel


class CreativeFactoryService:
    def __init__(self, engine: CreativeFactoryEngine | None = None) -> None:
        self.engine = engine or creative_factory_engine

    def reset(self) -> None:
        self.engine.reset()

    def ensure_ready(self) -> None:
        self.engine.ensure_seed()

    def status(self) -> dict[str, Any]:
        self.ensure_ready()
        return {
            "service": "creative_factory",
            "canonical": "platform_ai",
            "sprint": "36.9",
            "creative_types": [c.value for c in CreativeType],
            "modalities": [m.value for m in MediaModality],
            "channels": [c.value for c in PublishChannel],
            "statistics": self.engine.statistics(),
            "integrations": [
                "ai_runtime",
                "multi_agent_runtime",
                "project_memory",
                "context_engine",
                "workflow",
                "event_bus",
                "voice_runtime",
                "skills_sdk",
            ],
        }

    def list_brands(self) -> list[dict[str, Any]]:
        return [b.to_dict() for b in self.engine.list_brands()]

    def upsert_brand(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.upsert_brand(body).to_dict()

    def get_brand(self, brand_id: str) -> dict[str, Any]:
        return self.engine.get_brand(brand_id).to_dict()

    def list_templates(self, **kwargs: Any) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self.engine.list_templates(**kwargs)]

    def create_project(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.create_project(body).to_dict()

    def list_projects(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in self.engine.list_projects()]

    async def generate(self, body: dict[str, Any]) -> dict[str, Any]:
        return (await self.engine.generate(body)).to_dict()

    def list_assets(self, **kwargs: Any) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self.engine.list_assets(**kwargs)]

    def get_asset(self, asset_id: str) -> dict[str, Any]:
        return self.engine.get_asset(asset_id).to_dict()

    def review_asset(self, asset_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        return self.engine.review_asset(
            asset_id,
            approve=bool(body.get("approve", True)),
            notes=str(body.get("notes") or ""),
        ).to_dict()

    def version_asset(self, asset_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.version_asset(asset_id, body).to_dict()

    def list_media(self, **kwargs: Any) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self.engine.list_media(**kwargs)]

    def store_media(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.store_media(body).to_dict()

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        return self.engine.search(query, limit=limit)

    def create_campaign(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.create_campaign(body).to_dict()

    def list_campaigns(self) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self.engine.list_campaigns()]

    def get_campaign(self, campaign_id: str) -> dict[str, Any]:
        return self.engine.get_campaign(campaign_id).to_dict()

    def attach_creative(self, campaign_id: str, asset_id: str) -> dict[str, Any]:
        return self.engine.attach_creative(campaign_id, asset_id).to_dict()

    def campaign_analytics(self, campaign_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.engine.campaign_analytics(campaign_id, body)

    async def publish(self, body: dict[str, Any]) -> dict[str, Any]:
        return (await self.engine.publish(body)).to_dict()

    def list_publish_jobs(self) -> list[dict[str, Any]]:
        return [j.to_dict() for j in self.engine.list_publish_jobs()]

    def run_scheduled(self) -> list[dict[str, Any]]:
        return self.engine.run_scheduled()

    def list_providers(self, *, modality: str | None = None) -> list[dict[str, Any]]:
        return self.engine.media.list_providers(modality=modality)

    async def media_generate(self, body: dict[str, Any]) -> dict[str, Any]:
        brand = None
        brand_id = body.get("brand_id")
        if brand_id:
            try:
                brand = self.engine.get_brand(str(brand_id))
            except KeyError:
                brand = None
        return await self.engine.media.generate(
            str(body.get("modality") or "text"),
            str(body.get("prompt") or ""),
            preferred=body.get("provider_id"),
            brand=brand,
        )

    def statistics(self) -> dict[str, Any]:
        return self.engine.statistics()

    def timeline(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return self.engine.timeline(limit=limit)

    def analytics_dashboard(self) -> dict[str, Any]:
        return self.engine.analytics_dashboard()

    # --- Integrations ---

    async def for_ai_runtime(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        asset = await self.generate(
            {
                "creative_type": body.get("creative_type") or "social_post",
                "topic": body.get("topic") or "AI Runtime launch",
                "audience": body.get("audience") or "operators",
                "modality": body.get("modality") or "text",
            }
        )
        return {"consumer": "ai_runtime", "asset": asset}

    async def for_multi_agent(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        asset = await self.generate(
            {
                "creative_type": body.get("creative_type") or "blog_article",
                "topic": body.get("topic") or "multi-agent collaboration",
                "audience": "engineering leads",
                "modality": "text",
            }
        )
        return {"consumer": "multi_agent_runtime", "asset": asset}

    async def for_project_memory(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        asset = await self.generate(
            {
                "creative_type": "marketing_report",
                "topic": body.get("topic") or "campaign learnings",
                "modality": "text",
            }
        )
        try:
            from platform_memory.project_memory_service import project_memory_service

            await project_memory_service.remember(
                {
                    "kind": "agent",
                    "layer": "working",
                    "title": f"Creative: {asset.get('title')}",
                    "content": str(asset.get("content") or "")[:2000],
                    "agent_id": "creative_factory",
                    "project_id": body.get("project_id") or "proj_ados",
                }
            )
        except Exception:
            pass
        return {"consumer": "project_memory", "asset": asset}

    async def for_context_engine(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        ctx = None
        try:
            from platform_memory.service import context_engine_service

            ctx = await context_engine_service.for_ai_runtime(
                {"query": body.get("query") or "brand voice", "use_project_memory": False}
            )
        except Exception as exc:  # noqa: BLE001
            ctx = {"error": str(exc)}
        asset = await self.generate(
            {
                "creative_type": "email_campaign",
                "topic": body.get("topic") or "context-aware outreach",
                "prompt": f"Write email using context: {ctx}",
                "modality": "text",
            }
        )
        return {"consumer": "context_engine", "context": ctx, "asset": asset}

    async def for_workflow(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        asset = await self.generate(
            {
                "creative_type": body.get("creative_type") or "advertisement",
                "topic": body.get("topic") or "workflow-driven launch",
                "modality": "text",
            }
        )
        campaign = self.create_campaign(
            {
                "name": body.get("name") or "Workflow Campaign",
                "objective": "conversion",
                "channels": body.get("channels") or ["telegram", "linkedin"],
                "creative_ids": [asset["asset_id"]],
                "budget": float(body.get("budget") or 1000),
            }
        )
        return {"consumer": "workflow", "asset": asset, "campaign": campaign}

    async def for_event_bus(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        asset = await self.generate(
            {
                "creative_type": "social_post",
                "topic": body.get("topic") or "event-driven announce",
                "modality": "text",
            }
        )
        event = {
            "type": "creative.generated",
            "asset_id": asset.get("asset_id"),
            "source": "creative_factory",
        }
        try:
            from platform_events.service import event_bus_service  # type: ignore

            if hasattr(event_bus_service, "publish"):
                await event_bus_service.publish(event)
        except Exception:
            pass
        return {"consumer": "event_bus", "asset": asset, "event": event}

    async def for_voice(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        parsed = None
        try:
            from platform_ai.voice_service import voice_runtime_service

            parsed = voice_runtime_service.parse(
                str(body.get("transcript") or "create social post about enterprise launch")
            )
        except Exception as exc:  # noqa: BLE001
            parsed = {"error": str(exc)}
        topic = "enterprise launch"
        if isinstance(parsed, dict):
            topic = str(parsed.get("slots", {}).get("topic") or parsed.get("intent") or topic)
        asset = await self.generate(
            {
                "creative_type": "social_post",
                "topic": topic,
                "modality": "text",
            }
        )
        return {"consumer": "voice_runtime", "voice": parsed, "asset": asset}

    async def for_skills_sdk(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        skill_exe = None
        try:
            from platform_ai.skills_sdk_service import skills_sdk_service

            skill_exe = await skills_sdk_service.execute(
                {
                    "skill_id": body.get("skill_id") or "skill.local_draft",
                    "input": {"task": "creative brief"},
                    "auto_install": True,
                    "agent_id": "creative_factory",
                }
            )
        except Exception as exc:  # noqa: BLE001
            skill_exe = {"error": str(exc)}
        asset = await self.generate(
            {
                "creative_type": "sales_proposal",
                "topic": body.get("topic") or "skills-powered proposal",
                "modality": "text",
            }
        )
        return {"consumer": "skills_sdk", "skill_execution": skill_exe, "asset": asset}


creative_factory_service = CreativeFactoryService()
