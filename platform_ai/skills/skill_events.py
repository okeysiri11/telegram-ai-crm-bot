# Skill event bus integration.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class SkillExecutedEvent(BaseEvent):
    skill_id: str = ""
    execution_id: str = ""
    plugin_id: str = ""
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    cached: bool = False


@dataclass(kw_only=True)
class SkillFailedEvent(BaseEvent):
    skill_id: str = ""
    execution_id: str = ""
    plugin_id: str = ""
    error: str = ""


@dataclass(kw_only=True)
class SkillLoadedEvent(BaseEvent):
    skill_id: str = ""
    version: str = ""


@dataclass(kw_only=True)
class SkillDisabledEvent(BaseEvent):
    skill_id: str = ""


@dataclass(kw_only=True)
class SkillCostUpdatedEvent(BaseEvent):
    skill_id: str = ""
    cost_usd: float = 0.0
    avg_cost_usd: float = 0.0


async def publish_skill_event(event: BaseEvent) -> None:
    from events.publisher import publish_skill

    await publish_skill(event, wait=True)
