# Architecture report generator — ARCHITECTURE_REPORT.md output.

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from platform_architecture.certification import ArchitectureCertification
from platform_architecture.dependency_graph import DependencyGraphReport
from platform_architecture.rules import ROOT, ValidationSummary, ViolationSeverity


def generate_architecture_report(
    *,
    summaries: list[ValidationSummary],
    graph: DependencyGraphReport,
    certification: ArchitectureCertification,
    output_path: Path | None = None,
) -> Path:
    path = output_path or (ROOT / "ARCHITECTURE_REPORT.md")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines: list[str] = [
        "# Architecture Report",
        "",
        f"> Generated automatically on {now}",
        "",
        "## Executive Summary",
        "",
        f"- **Grade:** {certification.grade.value}",
        f"- **Architecture Score:** {certification.architecture_score}/100",
        f"- **Quality Gates:** {'PASSED' if certification.quality_gates_passed else 'FAILED'}",
        f"- **Modules in graph:** {graph.node_count}",
        f"- **Dependency edges:** {graph.edge_count}",
        f"- **Cycles:** {len(graph.cycles)}",
        "",
        certification.summary,
        "",
    ]

    if certification.gate_failures:
        lines.extend(["## Quality Gate Failures", ""])
        for item in certification.gate_failures:
            lines.append(f"- {item}")
        lines.append("")

    lines.extend(["## Validation Summary", ""])
    lines.append("| Domain | Status | Coverage | Violations |")
    lines.append("|--------|--------|----------|------------|")
    for summary in summaries:
        critical = sum(1 for v in summary.violations if v.severity == ViolationSeverity.CRITICAL)
        status = "PASS" if summary.passed else "FAIL"
        lines.append(
            f"| {summary.name} | {status} | {summary.validation_pct}% | {critical} critical / {len(summary.violations)} total |"
        )
    lines.append("")

    lines.extend(["## Dependency Graph", ""])
    lines.append("```mermaid")
    lines.append("flowchart TD")
    layer_nodes: dict[str, list[str]] = {}
    for node in graph.nodes.values():
        layer_nodes.setdefault(node.layer, []).append(node.path)
    for layer, nodes in sorted(layer_nodes.items()):
        safe = layer.replace(" ", "_")
        lines.append(f"  subgraph {safe}[{layer}]")
        for item in sorted(nodes)[:8]:
            node_id = item.replace("/", "_").replace(".", "_")
            lines.append(f"    {node_id}[{item}]")
        if len(nodes) > 8:
            lines.append(f"    {safe}_more[...+{len(nodes) - 8} modules]")
        lines.append("  end")
    lines.append("```")
    lines.append("")

    if graph.cycles:
        lines.extend(["### Dependency Cycles", ""])
        for cycle in graph.cycles:
            lines.append(f"- `{' -> '.join(cycle)}`")
        lines.append("")

    if graph.layer_violations:
        lines.extend(["## Layer Violations", ""])
        for item in graph.layer_violations[:30]:
            lines.append(f"- **[{item.rule}]** `{item.path}` — {item.detail}")
        lines.append("")

    for summary in summaries:
        critical = [v for v in summary.violations if v.severity == ViolationSeverity.CRITICAL]
        if not critical:
            continue
        lines.extend([f"## {summary.name.title()} Violations", ""])
        for item in critical[:25]:
            lines.append(f"- **[{item.rule}]** `{item.path}` — {item.detail}")
        if len(critical) > 25:
            lines.append(f"- ... and {len(critical) - 25} more")
        lines.append("")

    lines.extend(["## Certification Categories", ""])
    lines.append("| Category | Score | Weight | Status |")
    lines.append("|----------|-------|--------|--------|")
    for cat in certification.categories:
        lines.append(f"| {cat.name} | {cat.score} | {cat.weight} | {'PASS' if cat.passed else 'WARN'} |")
    lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def generate_architecture_certificate(
    certification: ArchitectureCertification,
    *,
    output_path: Path | None = None,
) -> Path:
    path = output_path or (ROOT / "ARCHITECTURE_CERTIFICATE.md")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "# Architecture Certificate",
        "",
        f"> Issued: {now}",
        "",
        "## Result",
        "",
        f"**{certification.grade.value}**",
        "",
        f"Architecture Score: **{certification.architecture_score}/100**",
        "",
        "Quality Gates: **" + ("PASSED" if certification.quality_gates_passed else "FAILED") + "**",
        "",
        "## Evaluation",
        "",
        "| Area | Score | Status | Notes |",
        "|------|-------|--------|-------|",
    ]
    for cat in certification.categories:
        lines.append(f"| {cat.name} | {cat.score} | {'PASS' if cat.passed else 'WARN/FAIL'} | {cat.notes} |")

    lines.extend(["", "## Minimum Thresholds", ""])
    lines.extend([
        "- Architecture Score ≥ 90",
        "- No boundary violations (critical)",
        "- No dependency cycles",
        "- No forbidden imports",
        "- 100% API validation",
        "- 100% SDK validation",
        "- 100% workflow validation",
        "",
    ])

    if certification.gate_failures:
        lines.extend(["## Failed Gates", ""])
        for item in certification.gate_failures:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*This certificate is generated automatically by Architecture Governance CI.*")
    lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
