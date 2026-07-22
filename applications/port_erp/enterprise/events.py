# Sprint 9.8 — enterprise / network / production events.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from applications.port_erp.enterprise.models import _ts


@dataclass
class PartnerRegisteredEvent:
    partner_id: str
    partner_type: str
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": "partner.registered",
            "partner_id": self.partner_id,
            "partner_type": self.partner_type,
            "created_at": self.created_at,
        }


@dataclass
class IntegrationConnectedEvent:
    link_id: str
    target: str
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": "integration.connected",
            "link_id": self.link_id,
            "target": self.target,
            "created_at": self.created_at,
        }


@dataclass
class ReleaseVerifiedEvent:
    report_id: str
    ready: bool
    version: str
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": "release.verified",
            "report_id": self.report_id,
            "ready": self.ready,
            "version": self.version,
            "created_at": self.created_at,
        }
