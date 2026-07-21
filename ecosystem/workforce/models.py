# Workforce models — Sprint 7.4.

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


class ExecutiveRole(str, enum.Enum):
    CEO = "chief_executive_ai"
    COO = "chief_operations_ai"
    CFO = "chief_financial_ai"
    CSO = "chief_sales_ai"
    CMO = "chief_marketing_ai"
    CTO = "chief_technology_ai"
    CLO = "chief_legal_ai"
    CAO = "chief_analytics_ai"


class DepartmentType(str, enum.Enum):
    SALES = "sales"
    FINANCE = "finance"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    SUPPORT = "support"
    DEVELOPMENT = "development"
    LEGAL = "legal"
    LOGISTICS = "logistics"


class SpecialistType(str, enum.Enum):
    SALES = "sales_specialist"
    FINANCIAL = "financial_specialist"
    MARKETING = "marketing_specialist"
    DEVELOPER = "developer_specialist"
    SUPPORT = "support_specialist"
    LAW = "law_specialist"
    ANALYTICS = "analytics_specialist"
    INVENTORY = "inventory_specialist"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    BLOCKED = "blocked"


class PlanHorizon(str, enum.Enum):
    COMPANY = "company"
    DEPARTMENT = "department"
    QUARTERLY = "quarterly"
    WEEKLY = "weekly"
    DAILY = "daily"


DEPARTMENT_EXECUTIVE: dict[DepartmentType, ExecutiveRole] = {
    DepartmentType.SALES: ExecutiveRole.CSO,
    DepartmentType.FINANCE: ExecutiveRole.CFO,
    DepartmentType.MARKETING: ExecutiveRole.CMO,
    DepartmentType.OPERATIONS: ExecutiveRole.COO,
    DepartmentType.SUPPORT: ExecutiveRole.COO,
    DepartmentType.DEVELOPMENT: ExecutiveRole.CTO,
    DepartmentType.LEGAL: ExecutiveRole.CLO,
    DepartmentType.LOGISTICS: ExecutiveRole.COO,
}

SPECIALIST_DEPARTMENT: dict[SpecialistType, DepartmentType] = {
    SpecialistType.SALES: DepartmentType.SALES,
    SpecialistType.FINANCIAL: DepartmentType.FINANCE,
    SpecialistType.MARKETING: DepartmentType.MARKETING,
    SpecialistType.DEVELOPER: DepartmentType.DEVELOPMENT,
    SpecialistType.SUPPORT: DepartmentType.SUPPORT,
    SpecialistType.LAW: DepartmentType.LEGAL,
    SpecialistType.ANALYTICS: DepartmentType.OPERATIONS,
    SpecialistType.INVENTORY: DepartmentType.LOGISTICS,
}


@dataclass
class ExecutiveAgent:
    executive_id: str = field(default_factory=_id)
    role: ExecutiveRole = ExecutiveRole.CEO
    name: str = ""
    authority_level: int = 100
    departments: list[str] = field(default_factory=list)
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "executive_id": self.executive_id,
            "role": self.role.value,
            "name": self.name,
            "authority_level": self.authority_level,
            "departments": list(self.departments),
            "is_active": self.is_active,
            "metadata": dict(self.metadata),
        }


@dataclass
class Department:
    department_id: str = field(default_factory=_id)
    department_type: DepartmentType = DepartmentType.OPERATIONS
    name: str = ""
    executive_role: ExecutiveRole = ExecutiveRole.COO
    manager_id: str = ""
    workload: int = 0
    capacity: int = 100
    is_active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "department_id": self.department_id,
            "department_type": self.department_type.value,
            "name": self.name,
            "executive_role": self.executive_role.value,
            "manager_id": self.manager_id,
            "workload": self.workload,
            "capacity": self.capacity,
            "is_active": self.is_active,
            "utilization": round(self.workload / self.capacity, 2) if self.capacity else 0,
        }


@dataclass
class SpecialistAgent:
    specialist_id: str = field(default_factory=_id)
    specialist_type: SpecialistType = SpecialistType.SUPPORT
    name: str = ""
    department_type: DepartmentType = DepartmentType.SUPPORT
    skills: list[str] = field(default_factory=list)
    active_tasks: int = 0
    max_tasks: int = 10
    is_active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "specialist_id": self.specialist_id,
            "specialist_type": self.specialist_type.value,
            "name": self.name,
            "department_type": self.department_type.value,
            "skills": list(self.skills),
            "active_tasks": self.active_tasks,
            "max_tasks": self.max_tasks,
            "is_active": self.is_active,
        }


@dataclass
class WorkforceTask:
    task_id: str = field(default_factory=_id)
    title: str = ""
    description: str = ""
    department_type: DepartmentType = DepartmentType.OPERATIONS
    specialist_id: str = ""
    executive_role: ExecutiveRole | None = None
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    requires_approval: bool = False
    approved_by: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    application_id: str = ""
    created_at: float = field(default_factory=_ts)
    completed_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "department_type": self.department_type.value,
            "specialist_id": self.specialist_id,
            "executive_role": self.executive_role.value if self.executive_role else None,
            "priority": self.priority.value,
            "status": self.status.value,
            "requires_approval": self.requires_approval,
            "approved_by": self.approved_by,
            "result": dict(self.result),
            "application_id": self.application_id,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


@dataclass
class ExecutiveDecision:
    decision_id: str = field(default_factory=_id)
    executive_role: ExecutiveRole = ExecutiveRole.CEO
    title: str = ""
    rationale: str = ""
    approved: bool = True
    task_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "executive_role": self.executive_role.value,
            "title": self.title,
            "rationale": self.rationale,
            "approved": self.approved,
            "task_id": self.task_id,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class Objective:
    objective_id: str = field(default_factory=_id)
    title: str = ""
    horizon: PlanHorizon = PlanHorizon.COMPANY
    department_type: DepartmentType | None = None
    target_metric: str = ""
    target_value: float = 0.0
    current_value: float = 0.0
    status: str = "active"
    owner_role: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective_id": self.objective_id,
            "title": self.title,
            "horizon": self.horizon.value,
            "department_type": self.department_type.value if self.department_type else None,
            "target_metric": self.target_metric,
            "target_value": self.target_value,
            "current_value": self.current_value,
            "status": self.status,
            "owner_role": self.owner_role,
            "progress": round(self.current_value / self.target_value, 2) if self.target_value else 0,
            "created_at": self.created_at,
        }


@dataclass
class WorkPlan:
    plan_id: str = field(default_factory=_id)
    horizon: PlanHorizon = PlanHorizon.WEEKLY
    title: str = ""
    department_type: DepartmentType | None = None
    items: list[dict[str, Any]] = field(default_factory=list)
    status: str = "active"
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "horizon": self.horizon.value,
            "title": self.title,
            "department_type": self.department_type.value if self.department_type else None,
            "items": list(self.items),
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Escalation:
    escalation_id: str = field(default_factory=_id)
    task_id: str = ""
    from_level: str = ""
    to_role: ExecutiveRole = ExecutiveRole.CEO
    reason: str = ""
    resolved: bool = False
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "escalation_id": self.escalation_id,
            "task_id": self.task_id,
            "from_level": self.from_level,
            "to_role": self.to_role.value,
            "reason": self.reason,
            "resolved": self.resolved,
            "created_at": self.created_at,
        }


@dataclass
class CollaborationSession:
    session_id: str = field(default_factory=_id)
    departments: list[str] = field(default_factory=list)
    topic: str = ""
    shared_memory: dict[str, Any] = field(default_factory=dict)
    shared_knowledge: list[str] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    status: str = "active"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "departments": list(self.departments),
            "topic": self.topic,
            "shared_memory": dict(self.shared_memory),
            "shared_knowledge": list(self.shared_knowledge),
            "decisions": list(self.decisions),
            "status": self.status,
            "created_at": self.created_at,
        }
