"""Voice Command Center models — Sprint 36.6 (extends platform_ai SoR)."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class VoiceMode(str, Enum):
    PUSH_TO_TALK = "push_to_talk"
    WAKE_WORD = "wake_word"
    CONTINUOUS = "continuous"


class VoiceSessionStatus(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    CLOSED = "closed"


class SpeechProviderId(str, Enum):
    OPENAI_REALTIME = "openai_realtime"
    WHISPER = "whisper"
    AZURE_SPEECH = "azure_speech"
    DEEPGRAM = "deepgram"
    GOOGLE_SPEECH = "google_speech"
    LOCAL_WHISPER = "local_whisper"


class VoiceIntent(str, Enum):
    OPEN_PAGE = "open_page"
    CREATE_PROJECT = "create_project"
    CREATE_TASK = "create_task"
    ASSIGN_EMPLOYEE = "assign_employee"
    SEARCH_KNOWLEDGE = "search_knowledge"
    OPEN_CRM = "open_crm"
    OPEN_ERP = "open_erp"
    LAUNCH_WORKFLOW = "launch_workflow"
    CALL_AI_AGENT = "call_ai_agent"
    GENERATE_REPORT = "generate_report"
    UNKNOWN = "unknown"


class CommandRisk(str, Enum):
    SAFE = "safe"
    CONFIRM = "confirm"
    DANGEROUS = "dangerous"


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class VoiceDevice:
    device_id: str
    name: str
    kind: str = "microphone"
    owner: str | None = None
    capabilities: list[str] = field(default_factory=lambda: ["mic", "vad", "streaming"])
    online: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VoiceProfile:
    profile_id: str
    name: str
    principal: str
    locale: str = "en-US"
    wake_word: str = "hey ados"
    mode: VoiceMode | str = VoiceMode.PUSH_TO_TALK
    preferred_provider: str = SpeechProviderId.WHISPER.value
    confirm_dangerous: bool = True
    roles: list[str] = field(default_factory=lambda: ["operator"])
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.mode, str):
            self.mode = VoiceMode(self.mode)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "principal": self.principal,
            "locale": self.locale,
            "wake_word": self.wake_word,
            "mode": self.mode.value if isinstance(self.mode, VoiceMode) else self.mode,
            "preferred_provider": self.preferred_provider,
            "confirm_dangerous": self.confirm_dangerous,
            "roles": list(self.roles),
            "metadata": dict(self.metadata),
        }


@dataclass
class VoiceSession:
    session_id: str
    principal: str
    profile_id: str | None = None
    device_id: str | None = None
    mode: VoiceMode | str = VoiceMode.PUSH_TO_TALK
    status: VoiceSessionStatus | str = VoiceSessionStatus.IDLE
    provider_id: str | None = None
    encrypted: bool = True
    cipher_hint: str = "aes-gcm-demo"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.mode, str):
            self.mode = VoiceMode(self.mode)
        if isinstance(self.status, str):
            self.status = VoiceSessionStatus(self.status)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "principal": self.principal,
            "profile_id": self.profile_id,
            "device_id": self.device_id,
            "mode": self.mode.value if isinstance(self.mode, VoiceMode) else self.mode,
            "status": self.status.value if isinstance(self.status, VoiceSessionStatus) else self.status,
            "provider_id": self.provider_id,
            "encrypted": self.encrypted,
            "cipher_hint": self.cipher_hint,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
        }


@dataclass
class ParsedCommand:
    intent: VoiceIntent | str
    confidence: float
    transcript: str
    entities: dict[str, str] = field(default_factory=dict)
    risk: CommandRisk | str = CommandRisk.SAFE
    route: str | None = None
    requires_confirmation: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.intent, str):
            self.intent = VoiceIntent(self.intent)
        if isinstance(self.risk, str):
            self.risk = CommandRisk(self.risk)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent.value if isinstance(self.intent, VoiceIntent) else self.intent,
            "confidence": self.confidence,
            "transcript": self.transcript,
            "entities": dict(self.entities),
            "risk": self.risk.value if isinstance(self.risk, CommandRisk) else self.risk,
            "route": self.route,
            "requires_confirmation": self.requires_confirmation,
        }


@dataclass
class VoiceCommand:
    command_id: str
    session_id: str
    transcript: str
    intent: str
    confidence: float
    entities: dict[str, Any] = field(default_factory=dict)
    risk: str = CommandRisk.SAFE.value
    status: str = "parsed"
    result: dict[str, Any] = field(default_factory=dict)
    approved_by: str | None = None
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VoiceHistoryEntry:
    history_id: str
    action: str
    session_id: str | None = None
    command_id: str | None = None
    principal: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TranscriptChunk:
    text: str
    is_final: bool = False
    provider_id: str = SpeechProviderId.WHISPER.value
    confidence: float = 0.9
    vad_active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
