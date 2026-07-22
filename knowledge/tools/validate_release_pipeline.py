#!/usr/bin/env python3
"""Validate Knowledge enterprise release pipeline artifacts exist."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
K = REPO / "knowledge"


def main() -> None:
    required = [
        "github/README.md",
        "architecture/README.md",
        "dashboard/README.md",
        "developer/README.md",
        "pipeline/README.md",
        "pipeline/EXECUTIVE_SUMMARY.md",
        "INDEX.md",
        "CHANGELOG.md",
        "releases/RELEASE_NOTES.md",
        "registries/APPLICATION_REGISTRY.md",
        "registries/AI_AGENT_REGISTRY.md",
    ]
    missing = [r for r in required if not (K / r).exists()]
    gh_required = [
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/CODEOWNERS",
        ".github/workflows/knowledge-validation.yml",
        ".github/ISSUE_TEMPLATE/bug_report.md",
    ]
    missing_gh = [r for r in gh_required if not (REPO / r).exists()]
    mermaid = 0
    arch = K / "architecture"
    if arch.exists():
        for p in arch.rglob("*.md"):
            if "```mermaid" in p.read_text(errors="ignore"):
                mermaid += 1
    report = {
        "status": "ok" if not missing and not missing_gh and mermaid >= 5 else "fail",
        "missing_knowledge": missing,
        "missing_github": missing_gh,
        "mermaid_architecture_pages": mermaid,
    }
    out = K / "pipeline" / "VALIDATION_RESULT.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "---\ntitle: Pipeline Validation Result\ntags:\n  - pipeline\n  - knowledge-2.0\n---\n\n"
        f"# Pipeline Validation Result\n\n```json\n{json.dumps(report, indent=2)}\n```\n"
    )
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["status"] == "ok" else 1)


if __name__ == "__main__":
    main()
