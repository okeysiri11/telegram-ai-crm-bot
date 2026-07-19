#!/usr/bin/env python3
"""Generate Sprint 1.5 architecture baseline artifacts under docs/."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOCS = ROOT / "docs"
BASELINE_DIR = DOCS / "architecture_baseline"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"report={path}")


def _module_graph_md(graph) -> str:
    layers: dict[str, list[str]] = defaultdict(list)
    for node in graph.nodes.values():
        layers[node.layer].append(node.path)
    lines = [
        "# Module Graph — Architecture Baseline",
        "",
        f"> Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "## Layers",
        "",
    ]
    for layer in sorted(layers):
        lines.append(f"### {layer} ({len(layers[layer])} modules)")
        lines.append("")
        for item in sorted(layers[layer])[:100]:
            lines.append(f"- `{item}`")
        if len(layers[layer]) > 100:
            lines.append(f"- ... +{len(layers[layer]) - 100} more")
        lines.append("")
    return "\n".join(lines) + "\n"


def _dependency_graph_md(graph) -> str:
    lines = [
        "# Dependency Graph — Architecture Baseline",
        "",
        f"> Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        f"- **Nodes:** {graph.node_count}",
        f"- **Edges:** {graph.edge_count}",
        f"- **Strict cycles:** {len(graph.cycles)}",
        "",
        "## Strict Cycles",
        "",
    ]
    if graph.cycles:
        for cycle in graph.cycles:
            lines.append(f"- `{' -> '.join(cycle)}`")
    else:
        lines.append("- None in governed layers")
    lines.extend(["", "## Sample Edges (first 200)", ""])
    for src, dst in graph.edges[:200]:
        lines.append(f"- `{src}` → `{dst}`")
    if len(graph.edges) > 200:
        lines.append(f"- ... +{len(graph.edges) - 200} more edges")
    lines.append("")
    return "\n".join(lines)


def _import_graph_md(graph) -> str:
    lines = [
        "# Import Graph — Architecture Baseline",
        "",
        f"> Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "## Cross-layer imports (governed)",
        "",
    ]
    for v in graph.layer_violations[:100]:
        lines.append(f"- **{v.severity.value}** `{v.path}` — {v.detail}")
    if not graph.layer_violations:
        lines.append("- No governed layer violations")
    lines.append("")
    return "\n".join(lines)


def _service_graph_md(graph) -> str:
    services = sorted(
        m for m, n in graph.nodes.items() if n.layer == "services" or m.startswith("services.")
    )
    lines = [
        "# Service Graph — Architecture Baseline",
        "",
        f"> Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        f"- **Service modules:** {len(services)}",
        "",
        "## Service → downstream dependencies",
        "",
    ]
    for svc in services[:80]:
        deps = sorted({dst for src, dst in graph.edges if src == svc})
        if not deps:
            continue
        lines.append(f"### `{svc}`")
        for dep in deps[:20]:
            layer = graph.nodes.get(dep, graph.nodes.get(dep.split(".")[0], None))
            label = layer.layer if layer else "unknown"
            lines.append(f"- `{dep}` ({label})")
        lines.append("")
    return "\n".join(lines)


def _baseline_summary(graph, gov) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return "\n".join(
        [
            "# Architecture Baseline — Platform Core v1.0.0-rc1",
            "",
            f"> Frozen baseline generated {now}",
            "",
            "## Scores",
            "",
            f"- **Architecture grade:** {gov.certification.grade.value}",
            f"- **Architecture score:** {gov.certification.architecture_score}/100",
            f"- **Quality gates:** {'PASS' if gov.certification.quality_gates_passed else 'FAIL'}",
            "",
            "## Graph Metrics",
            "",
            f"| Metric | Value |",
            f"|--------|------:|",
            f"| Modules | {graph.node_count} |",
            f"| Dependency edges | {graph.edge_count} |",
            f"| Strict governed cycles | {len(graph.cycles)} |",
            f"| Layer violations | {len(graph.layer_violations)} |",
            "",
            "## Baseline Artifacts",
            "",
            "- docs/architecture_baseline/MODULE_GRAPH.md",
            "- docs/architecture_baseline/DEPENDENCY_GRAPH.md",
            "- docs/architecture_baseline/IMPORT_GRAPH.md",
            "- docs/architecture_baseline/SERVICE_GRAPH.md",
            "- docs/architecture_baseline/graph.json",
            "",
            "## Platform Contracts",
            "",
            "- Management API: `/management/v1` (JWT/API key required)",
            "- Public API: `/api/v1` (frozen contract)",
            "- Event bus: `PlatformEventBus` + `events/crm_publisher.py` for CRM outbox",
            "- SDK: `platform_sdk/` → public services only (no repository/database)",
            "",
        ]
    )


def main() -> int:
    from platform_architecture.dependency_graph import build_dependency_graph
    from platform_architecture.governance import ArchitectureGovernance

    graph = build_dependency_graph(ROOT)
    gov = ArchitectureGovernance(ROOT).run_all(write_reports=True)

    _write(BASELINE_DIR / "MODULE_GRAPH.md", _module_graph_md(graph))
    _write(BASELINE_DIR / "DEPENDENCY_GRAPH.md", _dependency_graph_md(graph))
    _write(BASELINE_DIR / "IMPORT_GRAPH.md", _import_graph_md(graph))
    _write(BASELINE_DIR / "SERVICE_GRAPH.md", _service_graph_md(graph))
    _write(DOCS / "ARCHITECTURE_BASELINE.md", _baseline_summary(graph, gov))

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "nodes": graph.node_count,
        "edges": graph.edge_count,
        "strict_cycles": len(graph.cycles),
        "architecture_score": gov.certification.architecture_score,
        "modules": {m: {"layer": n.layer, "path": n.path} for m, n in graph.nodes.items()},
        "edges_list": [{"from": s, "to": d} for s, d in graph.edges],
        "strict_cycle_list": graph.cycles,
    }
    _write(BASELINE_DIR / "graph.json", json.dumps(payload, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
