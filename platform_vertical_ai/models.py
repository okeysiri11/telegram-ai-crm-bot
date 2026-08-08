"""Sprint 43.4 — Vertical AI Framework models.

Every industry vertical is described by configuration only.
Runtime stays UnifiedAiPipeline (Sprint 43.1–43.2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


Modality = Literal[
    "image",
    "video",
    "voice",
    "text",
    "prompt",
    "ads",
    "document",
    "presentation",
    "workflow",
    "calendar",
    "marketing",
]


@dataclass(frozen=True)
class VerticalMenuItem:
    id: str
    label: str
    action: str  # studio modality, agent, or special: history|favorites|settings|wizard|calendar|marketing
    modality: Modality | None = None
    agent: str | None = None


@dataclass(frozen=True)
class VerticalAgent:
    id: str
    name_ru: str
    role: str  # copywriter|designer|video|voice|marketing|crm|analytics
    capabilities: tuple[str, ...] = ()
    default_modality: Modality = "text"


@dataclass(frozen=True)
class PromptEntry:
    id: str
    category: str
    title: str
    seed: str


@dataclass(frozen=True)
class WizardQuestion:
    id: str
    question: str
    choices: tuple[str, ...] | None = None


@dataclass(frozen=True)
class CrmEntity:
    id: str
    name_ru: str


@dataclass(frozen=True)
class DocumentType:
    id: str
    name_ru: str


@dataclass(frozen=True)
class KnowledgeTopic:
    id: str
    title: str
    summary: str


@dataclass(frozen=True)
class VerticalConfig:
    """Single source of truth for one industry vertical."""

    id: str
    name_ru: str
    icon: str
    color: str
    description_ru: str
    menu: tuple[VerticalMenuItem, ...]
    agents: tuple[VerticalAgent, ...]
    scenarios: tuple[str, ...]
    wizard: tuple[WizardQuestion, ...]
    prompt_library: tuple[PromptEntry, ...]
    crm_entities: tuple[CrmEntity, ...] = ()
    document_types: tuple[DocumentType, ...] = ()
    knowledge: tuple[KnowledgeTopic, ...] = ()
    calendar_periods: tuple[int, ...] = (7, 14, 30, 90)
    marketing_offers: tuple[str, ...] = ()
    dashboard_widgets: tuple[str, ...] = ("history", "favorites", "calendar", "marketing")
    inherit: tuple[str, ...] = (
        "ai_chat",
        "ai_studio",
        "crm",
        "documents",
        "history",
        "favorites",
        "prompts",
        "automations",
        "analytics",
        "agents",
        "context",
        "search",
        "notifications",
        "rbac",
        "telegram",
        "web",
        "desktop",
        "mobile",
    )
    chain_steps: tuple[str, ...] = (
        "prompt",
        "image",
        "video",
        "voice",
        "music",
        "reels",
        "caption",
        "hashtags",
        "publish_ready",
    )
    enabled: bool = True
    complete: bool = False  # True = reference vertical (Beauty)

    def menu_labels(self) -> list[str]:
        return [m.label for m in self.menu]

    def find_menu(self, label: str) -> VerticalMenuItem | None:
        for m in self.menu:
            if m.label == label:
                return m
        return None

    def agent(self, agent_id: str) -> VerticalAgent | None:
        for a in self.agents:
            if a.id == agent_id:
                return a
        return None

    def prompts_by_category(self, category: str) -> list[PromptEntry]:
        return [p for p in self.prompt_library if p.category == category]

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name_ru": self.name_ru,
            "icon": self.icon,
            "color": self.color,
            "description_ru": self.description_ru,
            "complete": self.complete,
            "enabled": self.enabled,
            "menu": [{"id": m.id, "label": m.label, "action": m.action} for m in self.menu],
            "agents": [{"id": a.id, "name_ru": a.name_ru, "role": a.role} for a in self.agents],
            "scenarios": list(self.scenarios),
            "calendar_periods": list(self.calendar_periods),
            "inherit": list(self.inherit),
            "chain_steps": list(self.chain_steps),
        }
