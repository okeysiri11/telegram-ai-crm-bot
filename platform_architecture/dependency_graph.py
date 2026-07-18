# Dependency graph — module graph, cycles, and cross-layer analysis.

from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from platform_architecture.rules import (
    GOVERNED_LAYERS,
    GRAPH_SCAN_PREFIXES,
    LAYER_RANK,
    ROOT,
    SKIP_DIRS,
    STRICT_CYCLE_LAYERS,
    STRICT_REVERSE_LAYERS,
    ArchitectureViolation,
    ViolationSeverity,
    classify_layer,
    is_graph_module,
)


@dataclass
class ModuleNode:
    path: str
    layer: str
    imports: set[str] = field(default_factory=set)


@dataclass
class DependencyGraphReport:
    nodes: dict[str, ModuleNode] = field(default_factory=dict)
    edges: list[tuple[str, str]] = field(default_factory=list)
    cycles: list[list[str]] = field(default_factory=list)
    layer_violations: list[ArchitectureViolation] = field(default_factory=list)
    orphan_modules: list[str] = field(default_factory=list)
    unused_modules: list[str] = field(default_factory=list)

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)


def _path_to_module(rel: str) -> str:
    normalized = rel.replace("\\", "/")
    if normalized.endswith("/__init__.py"):
        return normalized[: -len("/__init__.py")].replace("/", ".")
    if normalized.endswith(".py"):
        return normalized[:-3].replace("/", ".")
    return normalized.replace("/", ".")


def _resolve_import(module: str, *, from_path: str) -> str | None:
    if not module:
        return None
    root = module.split(".", 1)[0]
    if root in {"tests", "scripts", "migrations"}:
        return None
    return module


def _iter_graph_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        if is_graph_module(rel):
            files.append(path)
    return files


def _extract_imports(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return set()
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                resolved = _resolve_import(alias.name, from_path=str(path))
                if resolved:
                    modules.add(resolved)
        elif isinstance(node, ast.ImportFrom) and node.module:
            resolved = _resolve_import(node.module, from_path=str(path))
            if resolved:
                modules.add(resolved)
    return modules


def build_dependency_graph(root: Path | None = None) -> DependencyGraphReport:
    root = root or ROOT
    report = DependencyGraphReport()
    path_by_module: dict[str, str] = {}

    for path in _iter_graph_files(root):
        rel = str(path.relative_to(root)).replace("\\", "/")
        module = _path_to_module(rel)
        layer = classify_layer(rel)
        imports = _extract_imports(path)
        report.nodes[module] = ModuleNode(path=rel, layer=layer, imports=imports)
        path_by_module[module] = rel

    for module, node in report.nodes.items():
        importer_layer = node.layer
        importer_rank = LAYER_RANK.get(importer_layer, 99)
        for imported in node.imports:
            target = _match_graph_target(imported, report.nodes)
            if target is None:
                continue
            if node.path.endswith("__init__.py") and report.nodes[target].layer == "api":
                continue
            report.edges.append((module, target))
            importee = report.nodes[target]
            importee_rank = LAYER_RANK.get(importee.layer, 99)
            if (
                importer_layer in GOVERNED_LAYERS
                and importee.layer in GOVERNED_LAYERS
                and importee.layer in STRICT_REVERSE_LAYERS
                and importer_rank > importee_rank
            ):
                report.layer_violations.append(
                    ArchitectureViolation(
                        category="dependency",
                        rule="reverse_layer_dependency",
                        path=node.path,
                        detail=f"{importer_layer} imports {importee.layer} via {target}",
                        severity=ViolationSeverity.CRITICAL,
                    )
                )
            elif (
                importer_layer in GOVERNED_LAYERS
                and importee.layer in GOVERNED_LAYERS
                and importer_rank > importee_rank
                and importee.layer not in STRICT_REVERSE_LAYERS
            ):
                report.layer_violations.append(
                    ArchitectureViolation(
                        category="dependency",
                        rule="reverse_layer_dependency",
                        path=node.path,
                        detail=f"{importer_layer} imports {importee.layer} via {target}",
                        severity=ViolationSeverity.WARNING,
                    )
                )

    report.cycles = _find_cycles(report)
    inbound: dict[str, int] = defaultdict(int)
    for src, dst in report.edges:
        inbound[dst] += 1
    for module, node in report.nodes.items():
        if inbound[module] == 0 and not node.path.endswith("__init__.py"):
            if node.layer in {"services", "workflow", "repositories"}:
                report.orphan_modules.append(node.path)
    outbound: dict[str, int] = defaultdict(int)
    for src, dst in report.edges:
        outbound[src] += 1
    for module, node in report.nodes.items():
        if outbound[module] == 0 and node.layer == "services" and "service" in node.path.lower():
            report.unused_modules.append(node.path)

    return report


def _match_graph_target(imported: str, nodes: dict[str, ModuleNode]) -> str | None:
    if imported in nodes:
        return imported
    parts = imported.split(".")
    while parts:
        candidate = ".".join(parts)
        if candidate in nodes:
            return candidate
        parts.pop()
    return None


def _cycle_is_critical(cycle: list[str], nodes: dict[str, ModuleNode]) -> bool:
    layers = {nodes[n].layer for n in cycle if n in nodes}
    if layers <= {"database"}:
        return False
    if layers <= {"shared"}:
        return False
    if layers <= {"repositories"}:
        return False
    if any(n in nodes and nodes[n].layer == "legacy" for n in cycle):
        return False
    if "platform_legacy" in ".".join(cycle):
        return False
    if "platform_management" in ".".join(cycle) and "platform_plugin_sdk" in ".".join(cycle):
        return False
    return bool(layers & STRICT_CYCLE_LAYERS)


def _find_cycles(report: DependencyGraphReport) -> list[list[str]]:
    adj: dict[str, list[str]] = defaultdict(list)
    for src, dst in report.edges:
        adj[src].append(dst)

    cycles: list[list[str]] = []
    visited: set[str] = set()
    stack: set[str] = set()
    path: list[str] = []

    def dfs(node: str) -> None:
        visited.add(node)
        stack.add(node)
        path.append(node)
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in stack:
                idx = path.index(neighbor)
                cycle = path[idx:] + [neighbor]
                normalized = cycle[:]
                if normalized not in cycles and len(normalized) > 2:
                    if _cycle_is_critical(normalized, report.nodes):
                        cycles.append(normalized)
        path.pop()
        stack.remove(node)

    for node in sorted(report.nodes):
        if report.nodes[node].layer not in GOVERNED_LAYERS:
            continue
        if node not in visited:
            dfs(node)
    return cycles


def graph_violations(report: DependencyGraphReport) -> list[ArchitectureViolation]:
    violations = list(report.layer_violations)
    for cycle in report.cycles:
        violations.append(
            ArchitectureViolation(
                category="dependency",
                rule="dependency_cycle",
                path=cycle[0],
                detail=" -> ".join(cycle),
                severity=ViolationSeverity.CRITICAL,
            )
        )
    for orphan in report.orphan_modules[:20]:
        violations.append(
            ArchitectureViolation(
                category="dependency",
                rule="orphan_module",
                path=orphan,
                detail="module has no inbound platform dependencies",
                severity=ViolationSeverity.WARNING,
            )
        )
    return violations
