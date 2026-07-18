# Certification gates — Sprint 1.5 pass/fail criteria.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CertificationGate:
    gate_id: str
    description: str
    passed: bool
    evidence: str
    severity: str = "critical"


@dataclass
class GateReport:
    gates: list[CertificationGate] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(g.passed for g in self.gates if g.severity == "critical")

    @property
    def pass_count(self) -> int:
        return sum(1 for g in self.gates if g.passed)

    @property
    def fail_count(self) -> int:
        return sum(1 for g in self.gates if not g.passed)


CERTIFICATION_GATES_SPEC: tuple[tuple[str, str], ...] = (
    ("repository_service_imports", "Repository → Service imports = 0"),
    ("sdk_repository_imports", "SDK → Repository imports = 0"),
    ("sdk_database_imports", "SDK → Database imports = 0"),
    ("unauthorized_admin_api", "Unauthorized Admin API = 0"),
    ("architecture_violations", "Architecture critical violations = 0"),
    ("ci_enforcement", "CI enforcement enabled (.github/workflows)"),
    ("documentation_sync", "Documentation synchronized (README reflects platform)"),
    ("security_tests", "Security tests pass"),
    ("architecture_audit", "Architecture audit passes (strict)"),
    ("dependency_audit", "Dependency audit passes (governed cycles)"),
    ("canonical_event_bus", "PlatformEventBus is canonical publish path"),
    ("release_readiness", "Release readiness = PASS"),
)
