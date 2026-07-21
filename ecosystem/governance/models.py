# Platform governance models — Sprint 7.6.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


class GovernanceDomain(str, enum.Enum):
    PLATFORM = "platform"
    APPLICATION = "application"
    AGENT = "agent"
    WORKFLOW = "workflow"
    DATA = "data"
    KNOWLEDGE = "knowledge"


class PolicyStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class ComplianceStatus(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"
    WAIVED = "waived"


class LifecycleState(str, enum.Enum):
    REGISTERED = "registered"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class LifecycleKind(str, enum.Enum):
    APPLICATION = "application"
    AGENT = "agent"
    PLUGIN = "plugin"
    WORKFLOW = "workflow"
    KNOWLEDGE = "knowledge"


class RiskSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(str, enum.Enum):
    POLICY = "policy"
    SECURITY = "security"
    OPERATIONAL = "operational"
    BUSINESS = "business"
    CONTINUITY = "continuity"
    DISASTER = "disaster"


@dataclass
class Policy:
    policy_id: str = field(default_factory=_id)
    name: str = ""
    domain: GovernanceDomain = GovernanceDomain.PLATFORM
    description: str = ""
    rules: list[str] = field(default_factory=list)
    status: PolicyStatus = PolicyStatus.ACTIVE
    retention_days: int = 365
    version: str = "1.0"
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "domain": self.domain.value,
            "description": self.description,
            "rules": list(self.rules),
            "status": self.status.value,
            "retention_days": self.retention_days,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class ComplianceCheck:
    check_id: str = field(default_factory=_id)
    policy_id: str = ""
    subject_type: str = ""
    subject_id: str = ""
    status: ComplianceStatus = ComplianceStatus.PENDING
    findings: list[str] = field(default_factory=list)
    auditor: str = "compliance_engine"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "policy_id": self.policy_id,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "status": self.status.value,
            "findings": list(self.findings),
            "auditor": self.auditor,
            "created_at": self.created_at,
        }


@dataclass
class AuditEntry:
    entry_id: str = field(default_factory=_id)
    action: str = ""
    actor: str = ""
    resource_type: str = ""
    resource_id: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "action": self.action,
            "actor": self.actor,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": dict(self.details),
            "created_at": self.created_at,
        }


@dataclass
class LifecycleRecord:
    record_id: str = field(default_factory=_id)
    kind: LifecycleKind = LifecycleKind.APPLICATION
    name: str = ""
    entity_id: str = ""
    version: str = "1.0.0"
    state: LifecycleState = LifecycleState.REGISTERED
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "kind": self.kind.value,
            "name": self.name,
            "entity_id": self.entity_id,
            "version": self.version,
            "state": self.state.value,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class RiskItem:
    risk_id: str = field(default_factory=_id)
    category: RiskCategory = RiskCategory.OPERATIONAL
    severity: RiskSeverity = RiskSeverity.MEDIUM
    title: str = ""
    description: str = ""
    mitigation: str = ""
    status: str = "open"
    related_policy_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_id": self.risk_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "mitigation": self.mitigation,
            "status": self.status,
            "related_policy_id": self.related_policy_id,
            "created_at": self.created_at,
        }


@dataclass
class FeatureFlag:
    flag_id: str = field(default_factory=_id)
    name: str = ""
    enabled: bool = False
    description: str = ""
    scope: str = "platform"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "flag_id": self.flag_id,
            "name": self.name,
            "enabled": self.enabled,
            "description": self.description,
            "scope": self.scope,
            "created_at": self.created_at,
        }


@dataclass
class LicenseRecord:
    license_id: str = field(default_factory=_id)
    organization_id: str = ""
    plan: str = "standard"
    seats: int = 10
    features: list[str] = field(default_factory=list)
    expires_at: float = 0.0
    is_active: bool = True
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "license_id": self.license_id,
            "organization_id": self.organization_id,
            "plan": self.plan,
            "seats": self.seats,
            "features": list(self.features),
            "expires_at": self.expires_at,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class CatalogEntry:
    entry_id: str = field(default_factory=_id)
    name: str = ""
    entry_type: str = "application"
    version: str = "1.0.0"
    owner: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "name": self.name,
            "entry_type": self.entry_type,
            "version": self.version,
            "owner": self.owner,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class GovernanceAction:
    action_id: str = field(default_factory=_id)
    action_type: str = ""
    domain: GovernanceDomain = GovernanceDomain.PLATFORM
    actor: str = "system"
    result: str = "executed"
    details: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "domain": self.domain.value,
            "actor": self.actor,
            "result": self.result,
            "details": dict(self.details),
            "created_at": self.created_at,
        }


@dataclass
class AccessReview:
    review_id: str = field(default_factory=_id)
    subject_id: str = ""
    reviewer: str = ""
    status: str = "pending"
    findings: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "subject_id": self.subject_id,
            "reviewer": self.reviewer,
            "status": self.status,
            "findings": list(self.findings),
            "created_at": self.created_at,
        }
