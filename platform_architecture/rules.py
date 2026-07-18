# Architecture rules — executable contracts and quality gates.

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Known legacy handler DB leaks — must not grow (tracked debt).
LEGACY_HANDLER_VIOLATIONS_ALLOWLIST: frozenset[str] = frozenset({
    "handler_no_database|auto_vertical_handlers.py|imports database layer",
    "handler_no_database|automotive_partner_handlers.py|imports database layer",
    "handler_no_database|dealer_onboarding_handlers.py|imports database layer",
    "handler_no_database|handlers.py|imports database layer",
})

# Layer rank — lower number = higher layer (may import downward only).
LAYER_RANK: dict[str, int] = {
    "api": 0,
    "shared": 1,
    "services": 2,
    "workflow": 2,
    "repositories": 3,
    "database": 4,
    "plugins": 5,
    "legacy": 6,
    "unknown": 99,
}

LAYER_PATH_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("api", ("platform_management/", "api/", "routers/")),
    ("shared", ("platform_api/",)),
    ("repositories", ("repositories/",)),
    ("database", ("database/", "database_legacy")),
    ("plugins", ("plugins/",)),
    ("workflow", ("platform_workflows/", "workflow/")),
    ("legacy", (
        "handlers.py",
        "database_legacy.py",
        "openrouter.py",
        "platform_events_legacy.py",
        "services/pg_",
    )),
)

# Platform modules scanned for dependency graph (relative prefixes).
GRAPH_SCAN_PREFIXES: tuple[str, ...] = (
    "platform_",
    "platform_management/",
    "platform_api/",
    "platform_workflows/",
    "platform_plugin_sdk/",
    "platform_legacy/",
    "platform_configuration/",
    "repositories/",
    "database/",
    "services/",
    "events/",
    "plugins/",
    "src/platform/",
    "src/verticals/",
)

SKIP_DIRS = frozenset({".venv", "venv", "node_modules", "__pycache__", ".git", ".pytest_cache"})

FORBIDDEN_IMPORT_PREFIXES: dict[str, tuple[str, ...]] = {
    "plugins": ("repositories", "database", "database_legacy", "openrouter", "platform_ai.providers", "platform_ai.llm"),
    "platform_management": ("repositories", "database", "database_legacy", "sqlalchemy", "asyncpg"),
    "platform_workflows": ("openrouter", "platform_ai.providers", "platform_ai.llm", "platform_ai.ai_providers"),
    "platform_ai/skills": ("openrouter", "platform_ai.providers"),
}

SDK_FORBIDDEN_PREFIXES: tuple[str, ...] = (
    "repositories",
    "database",
    "database_legacy",
    "platform_ai.providers",
    "services.pg_",
    "handlers",
    "openrouter",
)

LEGACY_FORBIDDEN_PLATFORM_PREFIXES: tuple[str, ...] = (
    "platform_management",
    "platform_identity",
    "platform_configuration",
    "platform_workflows",
    "platform_observability",
    "platform_operations",
    "platform_plugins",
    "platform_storage",
    "platform_sdk",
    "platform_plugin_sdk",
    "platform_ai",
    "platform_events",
    "platform_integrations",
    "platform_jobs",
    "platform_realtime",
    "src.platform",
    "src.verticals",
)

LEGACY_PUBLIC_PREFIXES: tuple[str, ...] = (
    "platform_legacy",
    "platform_api.contracts",
    "platform_api.responses",
    "platform_api.versioning",
)

SHARED_MODULE_SUFFIXES: tuple[str, ...] = (
    "platform_management/response_models.py",
    "platform_management/permissions.py",
    "platform_management/exceptions.py",
    "platform_management/management_context.py",
    "platform_management/auth.py",
)

GOVERNED_LAYERS: frozenset[str] = frozenset({"api", "shared", "services", "repositories", "database", "workflow"})

STRICT_REVERSE_LAYERS: frozenset[str] = frozenset({"api", "repositories", "database"})

STRICT_CYCLE_LAYERS: frozenset[str] = frozenset({"api", "repositories", "database"})

WORKFLOW_DEFINITIONS_DIR = ROOT / "workflow" / "definitions"

KNOWN_SERVICE_NAMES: frozenset[str] = frozenset({
    "SmartAssignmentService",
    "NotificationService",
    "CRMService",
    "AuditService",
    "WorkflowService",
    "IdentityService",
})


class ViolationSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class CertificationGrade(str, Enum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS WITH WARNINGS"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class ArchitectureViolation:
    category: str
    rule: str
    path: str
    detail: str
    severity: ViolationSeverity = ViolationSeverity.CRITICAL

    def key(self) -> str:
        return f"{self.rule}|{self.path}|{self.detail}"


@dataclass(frozen=True, slots=True)
class QualityGates:
    min_architecture_score: int = 90
    allow_boundary_violations: bool = False
    allow_dependency_cycles: bool = False
    allow_forbidden_imports: bool = False
    min_api_validation_pct: float = 100.0
    min_sdk_validation_pct: float = 100.0
    min_workflow_validation_pct: float = 100.0


QUALITY_GATES = QualityGates()


@dataclass
class ValidationSummary:
    name: str
    passed: bool
    total_checks: int = 0
    passed_checks: int = 0
    violations: list[ArchitectureViolation] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def validation_pct(self) -> float:
        if self.total_checks == 0:
            return 100.0 if self.passed else 0.0
        return round(100.0 * self.passed_checks / self.total_checks, 2)


def classify_layer(rel_path: str) -> str:
    normalized = rel_path.replace("\\", "/")
    if normalized in SHARED_MODULE_SUFFIXES:
        return "shared"
    if normalized == "platform_management/management_router.py":
        return "api"
    if normalized.startswith("platform_management/"):
        return "shared"
    if normalized.startswith("platform_ai/"):
        return "services"
    if normalized.endswith("_router.py") or "/routers/" in normalized:
        return "api"
    if normalized.endswith("/__init__.py"):
        return "shared"
    for layer, prefixes in LAYER_PATH_RULES:
        for prefix in prefixes:
            if prefix.endswith(".py"):
                if normalized == prefix or normalized.endswith("/" + prefix):
                    return layer
            elif normalized.startswith(prefix):
                return layer
    if normalized.startswith("platform_") or normalized.startswith("src/") or normalized.startswith("events/"):
        return "services"
    if normalized == "startup.py":
        return "services"
    return "unknown"


def is_graph_module(rel_path: str) -> bool:
    normalized = rel_path.replace("\\", "/")
    if normalized.startswith("platform_architecture/"):
        return False
    if normalized.startswith("tests/") or normalized.startswith("scripts/") or normalized.startswith("migrations/"):
        return False
    return any(normalized.startswith(prefix) for prefix in GRAPH_SCAN_PREFIXES)
