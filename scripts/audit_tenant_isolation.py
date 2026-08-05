#!/usr/bin/env python3
"""Tenant isolation audit — Sprint 30.0 (TD-58).

Scans repositories/*.py for query methods that reference models with tenant_id
but never mention tenant_id / apply_tenant_filter in the same function body.

Exit 0 always (report-only) unless --strict is passed.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_DIR = ROOT / "repositories"


def _functions(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    out: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append(node)
    return out


def audit_file(path: Path) -> list[dict[str, str]]:
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [{"file": str(path), "issue": f"syntax_error:{exc}"}]

    findings: list[dict[str, str]] = []
    if "tenant_id" not in source and "apply_tenant_filter" not in source:
        # File never mentions tenant — may be non-tenant entity; note only
        return findings

    for fn in _functions(tree):
        body = ast.get_source_segment(source, fn) or ""
        if "select(" not in body and ".where(" not in body and "execute(" not in body:
            continue
        mentions_filter = (
            "tenant_id" in body
            or "apply_tenant_filter" in body
            or "require_tenant_id" in body
        )
        # Heuristic: query-like + no tenant mention inside function
        if not mentions_filter and ("select(" in body or "session.execute" in body):
            findings.append(
                {
                    "file": str(path.relative_to(ROOT)),
                    "function": fn.name,
                    "line": str(fn.lineno),
                    "issue": "query_without_tenant_mention",
                }
            )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()

    findings: list[dict[str, str]] = []
    for path in sorted(REPO_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue
        findings.extend(audit_file(path))

    findings = findings[: args.limit]
    print(f"tenant_isolation_audit findings={len(findings)}")
    for item in findings[:50]:
        print(f"  {item['file']}:{item.get('line', '?')} {item.get('function', '')} — {item['issue']}")
    if len(findings) > 50:
        print(f"  ... {len(findings) - 50} more")

    out = ROOT / "docs" / "TENANT_ISOLATION_AUDIT.md"
    lines = [
        "# Tenant Isolation Audit — Sprint 30.0",
        "",
        f"Scanned `{REPO_DIR.relative_to(ROOT)}/*.py`. Heuristic findings (not confirmed leaks):",
        "",
        f"**Count:** {len(findings)}",
        "",
        "| File | Function | Line | Issue |",
        "|---|---|---|---|",
    ]
    for item in findings:
        lines.append(
            f"| `{item['file']}` | `{item.get('function', '')}` | {item.get('line', '')} | {item['issue']} |"
        )
    lines.extend(
        [
            "",
            "## Remediation",
            "",
            "- Prefer `repositories.tenant_scope.apply_tenant_filter(..., required=True)`.",
            "- Cross-tenant admin tools must pass `required=False` explicitly and log the bypass.",
            "- See `docs/TENANT_ISOLATION.md`.",
            "",
        ]
    )
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")

    if args.strict and findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
