# Consolidation / duplicate architecture scanner — Sprint 32.3.
# Extends sprint review; lightweight heuristics (not a full AST rewrite).

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from platform_architecture.canonical_services import CANONICAL_SERVICES, canonical_summary
from platform_architecture.rules import ROOT


@dataclass
class ConsolidationFinding:
    code: str
    severity: str
    message: str
    path: str | None = None


@dataclass
class ConsolidationReport:
    passed: bool
    findings: list[ConsolidationFinding] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "findings": [f.__dict__ for f in self.findings],
            "metadata": self.metadata,
        }


FORBIDDEN_NEW_EVENT_BUS = re.compile(r"^class\s+\w*EventBus\b", re.M)
FORBIDDEN_PARALLEL_QUEUE = re.compile(
    r"^class\s+(UnifiedQueueArchitecture|PlatformCoreQueue)\b", re.M
)


class ConsolidationScanner:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ROOT

    def run(self) -> ConsolidationReport:
        findings: list[ConsolidationFinding] = []
        findings.extend(self._check_canonical_registry())
        findings.extend(self._check_duplicate_event_buses())
        findings.extend(self._check_canonical_paths_exist())
        findings.extend(self._check_deal_pipeline_entry())
        findings.extend(self._check_unified_queue())
        findings.extend(self._check_docs())

        critical = [f for f in findings if f.severity == "critical"]
        return ConsolidationReport(
            passed=len(critical) == 0,
            findings=findings,
            metadata={
                "canonical": canonical_summary(),
                "sprint": "32.3_consolidation",
            },
        )

    def _check_canonical_registry(self) -> list[ConsolidationFinding]:
        required = {
            "deal_pipeline",
            "workflow_engine",
            "knowledge_base",
            "event_bus",
            "notification_pipeline",
            "unified_queue",
            "secret_policy",
            "enterprise_metrics",
            "security_center",
        }
        missing = required - set(CANONICAL_SERVICES.keys())
        if missing:
            return [
                ConsolidationFinding(
                    code="CANONICAL_GAP",
                    severity="critical",
                    message=f"Canonical registry missing: {sorted(missing)}",
                )
            ]
        return [
            ConsolidationFinding(
                code="CANONICAL_OK",
                severity="info",
                message=f"Canonical registry lists {len(CANONICAL_SERVICES)} services",
            )
        ]

    def _check_canonical_paths_exist(self) -> list[ConsolidationFinding]:
        out: list[ConsolidationFinding] = []
        for key, meta in CANONICAL_SERVICES.items():
            rel = meta.get("path")
            if not rel:
                continue
            path = self.root / rel
            if not path.exists():
                out.append(
                    ConsolidationFinding(
                        code="CANONICAL_PATH_MISSING",
                        severity="critical",
                        message=f"Canonical path missing for {key}: {rel}",
                        path=rel,
                    )
                )
        if not out:
            out.append(
                ConsolidationFinding(
                    code="CANONICAL_PATHS_OK",
                    severity="info",
                    message="All canonical paths exist",
                )
            )
        return out

    def _check_duplicate_event_buses(self) -> list[ConsolidationFinding]:
        """Warn on new EventBus class definitions outside allowlisted legacy paths."""
        out: list[ConsolidationFinding] = []
        allow = {
            "events/event_bus.py",
            "platform_events_legacy.py",
            "ecosystem/communication/event_bus/bus.py",
            "applications/finance_enterprise/integration/event_bus.py",
            "applications/enterprise_hub/event_platform/event_bus.py",
            "applications/platform_builder/team_map/engine.py",
        }
        # Only scan a few high-risk trees for *new* definitions this sprint.
        scan_roots = [
            self.root / "services",
            self.root / "platform_architecture",
            self.root / "platform_jobs",
        ]
        for base in scan_roots:
            if not base.exists():
                continue
            for path in base.rglob("*.py"):
                if path.name in {"consolidation_scanner.py", "sprint_review.py"}:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                if FORBIDDEN_NEW_EVENT_BUS.search(text):
                    rel = str(path.relative_to(self.root))
                    if rel not in allow:
                        out.append(
                            ConsolidationFinding(
                                code="DUPLICATE_EVENT_BUS",
                                severity="critical",
                                message="New EventBus class outside allowlist — use PlatformEventBus",
                                path=rel,
                            )
                        )
        if not any(f.code == "DUPLICATE_EVENT_BUS" for f in out):
            out.append(
                ConsolidationFinding(
                    code="EVENT_BUS_SCAN_OK",
                    severity="info",
                    message="No new EventBus classes in scanned Core trees",
                )
            )
        return out

    def _check_deal_pipeline_entry(self) -> list[ConsolidationFinding]:
        path = self.root / "services/canonical_deal_pipeline.py"
        if not path.is_file():
            return [
                ConsolidationFinding(
                    code="DEAL_ENTRY_MISSING",
                    severity="critical",
                    message="Canonical deal pipeline entry missing",
                    path="services/canonical_deal_pipeline.py",
                )
            ]
        return [
            ConsolidationFinding(
                code="DEAL_ENTRY_OK",
                severity="info",
                message="Canonical deal pipeline entry present",
                path="services/canonical_deal_pipeline.py",
            )
        ]

    def _check_unified_queue(self) -> list[ConsolidationFinding]:
        path = self.root / "platform_jobs/unified_queue.py"
        if not path.is_file():
            return [
                ConsolidationFinding(
                    code="QUEUE_MISSING",
                    severity="critical",
                    message="Unified queue architecture missing",
                    path="platform_jobs/unified_queue.py",
                )
            ]
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lane in ("ai", "workflow", "background", "notification", "render"):
            if lane not in text:
                return [
                    ConsolidationFinding(
                        code="QUEUE_LANE_GAP",
                        severity="critical",
                        message=f"Unified queue missing lane: {lane}",
                        path="platform_jobs/unified_queue.py",
                    )
                ]
        if "dead_letter" not in text and "DEAD_LETTER" not in text:
            return [
                ConsolidationFinding(
                    code="QUEUE_DLQ_GAP",
                    severity="critical",
                    message="Unified queue missing dead-letter support",
                    path="platform_jobs/unified_queue.py",
                )
            ]
        return [
            ConsolidationFinding(
                code="QUEUE_OK",
                severity="info",
                message="Unified queue lanes + DLQ present",
                path="platform_jobs/unified_queue.py",
            )
        ]

    def _check_docs(self) -> list[ConsolidationFinding]:
        required = (
            "docs/CANONICAL_SERVICES.md",
            "docs/QUEUE_ARCHITECTURE.md",
            "docs/EVENT_BUS.md",
            "docs/SPRINT_32_3_RESULT.md",
            "docs/SECURITY_CENTER.md",
            "docs/ZERO_TRUST.md",
            "docs/SPRINT_32_4_RESULT.md",
        )
        out: list[ConsolidationFinding] = []
        for rel in required:
            if not (self.root / rel).is_file():
                out.append(
                    ConsolidationFinding(
                        code="DOC_MISSING",
                        severity="critical",
                        message=f"Missing consolidation doc: {rel}",
                        path=rel,
                    )
                )
            else:
                out.append(
                    ConsolidationFinding(
                        code="DOC_OK",
                        severity="info",
                        message=f"Doc present: {rel}",
                        path=rel,
                    )
                )
        return out


def run_consolidation_scan(root: Path | None = None) -> ConsolidationReport:
    return ConsolidationScanner(root).run()
