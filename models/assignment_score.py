# Assignment score domain types — smart assignment engine.

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from config import SMART_ASSIGNMENT_EXTRA_SEGMENTS


class AssignmentSegment(str, enum.Enum):
    AUTO = "AUTO"
    AGRO = "AGRO"
    REALTY = "REALTY"
    LEGAL = "LEGAL"
    LOGISTICS = "LOGISTICS"
    CRM = "CRM"
    OTHER = "OTHER"


class AssignmentStrategy(str, enum.Enum):
    SMART = "SMART"
    ROUND_ROBIN = "ROUND_ROBIN"
    LEAST_LOADED = "LEAST_LOADED"
    PRIORITY = "PRIORITY"
    WEIGHTED = "WEIGHTED"


class ManagerSpecialization(str, enum.Enum):
    AUTO = "AUTO"
    AGRO = "AGRO"
    REALTY = "REALTY"
    LEGAL = "LEGAL"
    MULTI = "MULTI"


# Vertical / request_type prefix → segment (extensible via env)
_SEGMENT_PREFIX_MAP: dict[str, AssignmentSegment] = {
    "auto": AssignmentSegment.AUTO,
    "agro": AssignmentSegment.AGRO,
    "realty": AssignmentSegment.REALTY,
    "legal": AssignmentSegment.LEGAL,
    "logistics": AssignmentSegment.LOGISTICS,
    "crm": AssignmentSegment.CRM,
}


def _load_extra_segments() -> dict[str, AssignmentSegment]:
    raw = SMART_ASSIGNMENT_EXTRA_SEGMENTS.strip()
    if not raw:
        return {}
    out: dict[str, AssignmentSegment] = {}
    for part in raw.split(","):
        key = part.strip().upper()
        if key:
            try:
                out[key.lower()] = AssignmentSegment(key)
            except ValueError:
                out[key.lower()] = AssignmentSegment.OTHER
    return out


def segment_from_vertical(vertical: str | None) -> AssignmentSegment:
    key = (vertical or "").strip().lower()
    if not key:
        return AssignmentSegment.OTHER
    merged = {**_SEGMENT_PREFIX_MAP, **_load_extra_segments()}
    return merged.get(key, AssignmentSegment.OTHER)


def segment_from_request_type(request_type: str | None) -> AssignmentSegment | None:
    if not request_type:
        return None
    prefix = request_type.split("_")[0].lower()
    merged = {**_SEGMENT_PREFIX_MAP, **_load_extra_segments()}
    return merged.get(prefix)


@dataclass(frozen=True)
class ScoreWeights:
    load: float = 0.40
    response: float = 0.25
    completed: float = 0.15
    priority: float = 0.10
    specialization: float = 0.10

    @classmethod
    def from_config(cls) -> ScoreWeights:
        from platform_configuration.config_provider import config_provider

        weights = config_provider.smart_assignment_weights()
        return cls(
            load=weights["load"],
            response=weights["response"],
            completed=weights["completed"],
            priority=weights["priority"],
            specialization=weights["specialization"],
        )

    @classmethod
    def from_env(cls) -> ScoreWeights:
        """Deprecated — use from_config()."""
        return cls.from_config()

    def normalized(self) -> ScoreWeights:
        total = self.load + self.response + self.completed + self.priority + self.specialization
        if total <= 0:
            return ScoreWeights()
        return ScoreWeights(
            load=self.load / total,
            response=self.response / total,
            completed=self.completed / total,
            priority=self.priority / total,
            specialization=self.specialization / total,
        )


@dataclass(frozen=True)
class ManagerCandidateMetrics:
    pool_id: str
    telegram_id: int
    name: str
    vertical: str
    specialization: str
    priority: int
    current_load: int
    average_response_seconds: float | None = None
    completed_requests: int = 0


@dataclass(frozen=True)
class ManagerCandidateScore:
    candidate: ManagerCandidateMetrics
    total_score: float
    breakdown: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pool_id": self.candidate.pool_id,
            "manager_name": self.candidate.name,
            "telegram_id": self.candidate.telegram_id,
            "total_score": round(self.total_score, 4),
            "breakdown": {k: round(v, 4) for k, v in self.breakdown.items()},
        }


@dataclass(frozen=True)
class AssignmentRecordSnapshot:
    id: str
    request_id: str | None
    request_number: str | None
    manager_pool_id: str
    manager_user_id: str | None
    manager_telegram_id: int
    segment: str
    score: float
    strategy: str
    assignment_time: datetime
    completed: bool
    response_time_seconds: int | None
    resolution_time_seconds: int | None
    specialization: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "request_id": self.request_id,
            "request_number": self.request_number,
            "manager_pool_id": self.manager_pool_id,
            "manager_user_id": self.manager_user_id,
            "manager_telegram_id": self.manager_telegram_id,
            "segment": self.segment,
            "score": self.score,
            "strategy": self.strategy,
            "assignment_time": self.assignment_time.isoformat(),
            "completed": self.completed,
            "response_time_seconds": self.response_time_seconds,
            "resolution_time_seconds": self.resolution_time_seconds,
            "specialization": self.specialization,
        }
