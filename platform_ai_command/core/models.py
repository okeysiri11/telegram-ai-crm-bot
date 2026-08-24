"""AI Command Center domain models."""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


class AttachmentKind(str, enum.Enum):
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    DOCUMENT = "document"
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    ARCHIVE = "archive"
    SCREENSHOT = "screenshot"
    CODE = "code"
    LINK = "link"
    VIDEO = "video"


class TaskKind(str, enum.Enum):
    CHAT = "chat"
    IMAGE = "image"
    VIDEO = "video"
    VOICE = "voice"
    DOCUMENT = "document"
    PRESENTATION = "presentation"
    CRM = "crm"
    ERP = "erp"
    WORKFLOW = "workflow"
    ANALYTICS = "analytics"
    PUBLISH = "publish"
    SEARCH = "search"
    OCR = "ocr"
    TRANSLATE = "translate"
    AGENT = "agent"
    UNKNOWN = "unknown"


@dataclass
class Attachment:
    kind: AttachmentKind
    name: str = ""
    ref: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandMessage:
    """Sprint 47.0 (Decision 5 / CC-3): tenant_id is the canonical org identifier
    going forward; organization_id is kept for backward compatibility and mirrors it.
    Both were previously unpopulated by every caller — cmd_chat (platform_ai_command/
    api/router.py) now resolves a real tenant_id server-side instead of leaving this
    dead."""

    text: str
    owner_id: str
    channel: str = "web"  # web|telegram|desktop|voice
    session_id: str | None = None
    attachments: list[Attachment] = field(default_factory=list)
    locale: str = "ru"
    role: str = "owner"
    organization_id: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    tenant_id: str | None = None

    def __post_init__(self) -> None:
        if self.tenant_id is None and self.organization_id is not None:
            self.tenant_id = self.organization_id
        elif self.organization_id is None and self.tenant_id is not None:
            self.organization_id = self.tenant_id

    @property
    def has_voice(self) -> bool:
        return any(a.kind == AttachmentKind.VOICE for a in self.attachments) or self.channel == "voice"


@dataclass
class RouteDecision:
    task_kind: TaskKind
    vertical: str | None
    agents: list[str]
    tools: list[str]
    providers_hint: list[str]
    access_level: str
    cost_estimate: float
    needs_clarify: bool = False
    clarify_question: str | None = None
    confidence: float = 0.8


@dataclass
class PlanStep:
    id: str
    title_ru: str
    tool: str
    agent: str | None = None
    modality: str = "text"
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandPlan:
    id: str
    message: CommandMessage
    route: RouteDecision
    steps: list[PlanStep]
    created_at: float = field(default_factory=time.time)

    @classmethod
    def new(cls, message: CommandMessage, route: RouteDecision, steps: list[PlanStep]) -> CommandPlan:
        return cls(id=str(uuid.uuid4()), message=message, route=route, steps=steps)


@dataclass
class CommandResult:
    plan_id: str
    status: str
    reply_ru: str
    hercules_job_ids: list[str] = field(default_factory=list)
    step_results: dict[str, Any] = field(default_factory=dict)
    cost: float = 0.0
    duration_sec: float = 0.0
    files: list[str] = field(default_factory=list)
    favorite: bool = False
    created_at: float = field(default_factory=time.time)

    def history_line_ru(self) -> str:
        return f"• {self.status} · ≈{self.cost:.3f} у.е. · {self.duration_sec:.1f}с · {self.reply_ru[:80]}"
