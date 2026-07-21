# Sprint 8.8 — Production / release events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class ApplicationValidatedEvent(BaseEvent):
    report_id: str = ""
    passed: int = 0
    failed: int = 0


@dataclass(kw_only=True)
class ProductionReadyEvent(BaseEvent):
    version: str = ""
    status: str = ""
    score: float = 0.0


@dataclass(kw_only=True)
class ReleaseCreatedEvent(BaseEvent):
    release_id: str = ""
    version: str = ""
    release_type: str = ""


@dataclass(kw_only=True)
class DeploymentVerifiedEvent(BaseEvent):
    version: str = ""
    verified: bool = False


@dataclass(kw_only=True)
class CertificationCompletedEvent(BaseEvent):
    release_id: str = ""
    certified: bool = False
    version: str = ""
