"""Sprint 43.1 — Unified AI Task models (channel-agnostic)."""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


class AiTaskStatus(str, enum.Enum):
    """Russian-first pipeline statuses (canonical)."""

    CREATED = "создана"
    QUEUED = "в_очереди"
    PREPARING = "подготавливается"
    GENERATING = "генерируется"
    PROCESSING = "обрабатывается"
    DONE = "готово"
    ERROR = "ошибка"
    CANCELLED = "отменена"
    RETRY = "повтор"


class AiModality(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    VOICE = "voice"
    TEXT = "text"
    DOCUMENT = "document"
    PRESENTATION = "presentation"
    ADS = "ads"
    PROMPT = "prompt"


class AiChannel(str, enum.Enum):
    TELEGRAM = "telegram"
    WEB = "web"
    DESKTOP = "desktop"
    MOBILE = "mobile"
    REST = "rest"
    AUTOMATION = "automation"
    WORKFLOW = "workflow"


@dataclass
class AiTaskRequest:
    owner_id: str
    modality: str
    prompt: str
    channel: str = AiChannel.TELEGRAM.value
    tenant_id: str = "default"
    preferred_provider: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    studio_id: str | None = None
    vertical: str | None = None
    optimize_prompt: bool = True


@dataclass
class AiTaskRecord:
    id: str
    owner_id: str
    tenant_id: str
    channel: str
    modality: str
    prompt: str
    optimized_prompt: str
    status: str = AiTaskStatus.CREATED.value
    provider_id: str | None = None
    cost_estimate: float = 0.0
    credits_reserved: float = 0.0
    progress: int = 0
    source: str = "pipeline"
    studio_id: str | None = None
    vertical: str | None = None
    platform_job_id: str | None = None
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    favorite: bool = False
    cache_hit: bool = False
    history: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None

    @staticmethod
    def new(req: AiTaskRequest, *, optimized_prompt: str) -> "AiTaskRecord":
        return AiTaskRecord(
            id=str(uuid.uuid4()),
            owner_id=req.owner_id,
            tenant_id=req.tenant_id,
            channel=req.channel,
            modality=req.modality,
            prompt=req.prompt,
            optimized_prompt=optimized_prompt,
            studio_id=req.studio_id,
            vertical=req.vertical,
            meta=dict(req.meta),
            source=req.channel,
        )

    def append_history(self, event: str, **extra: Any) -> None:
        self.history.append({"ts": time.time(), "event": event, **extra})

    def duration_sec(self) -> float:
        if self.started_at and self.finished_at:
            return round(self.finished_at - self.started_at, 3)
        if self.started_at:
            return round(time.time() - self.started_at, 3)
        return 0.0

    def status_line_ru(self) -> str:
        provider = self.provider_id or "—"
        cache = " · кэш" if self.cache_hit else ""
        return (
            f"#{self.id[:8]} · {self.modality} · {self.status} · "
            f"{self.progress}% · AI: {provider} · ≈{self.cost_estimate:.3f} у.е. · "
            f"{self.duration_sec()}с{cache}"
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["duration_sec"] = self.duration_sec()
        return d


# Post-generation workflow (channel-agnostic labels RU).
POST_GEN_WORKFLOW_RU: tuple[tuple[str, str], ...] = (
    ("video", "Создать видео"),
    ("voice", "Создать озвучку"),
    ("music", "Создать музыку"),
    ("ads", "Создать рекламу"),
    ("publish", "Создать публикацию"),
    ("schedule", "Запланировать публикацию"),
    ("send_client", "Отправить клиенту"),
)

BEAUTY_STUDIO_PRODUCTS: tuple[str, ...] = (
    "Instagram",
    "TikTok",
    "Stories",
    "Reels",
    "Прайсы",
    "Акции",
    "Видео",
    "Баннеры",
    "До/После",
    "Описание услуг",
    "Ответы клиентам",
    "Контент-план",
    "Маркетинговый календарь",
    "Хештеги",
    "Сценарии",
)
