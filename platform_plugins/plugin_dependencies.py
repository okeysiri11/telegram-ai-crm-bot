# Plugin dependency resolution and cycle detection.

from __future__ import annotations

import re
from typing import Iterable

from platform_plugins.exceptions import PluginCycleError, PluginDependencyError, PluginNotFoundError
from platform_plugins.models import DependencySpec, PluginRecord, PluginState

_SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)")


def parse_version(version: str) -> tuple[int, int, int]:
    match = _SEMVER.match(version.strip())
    if not match:
        raise PluginDependencyError(f"Invalid version: {version}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def version_satisfies(actual: str, constraint: str) -> bool:
    actual_v = parse_version(actual)
    constraint = constraint.strip()
    if constraint.startswith(">="):
        required = parse_version(constraint[2:].strip())
        return actual_v >= required
    if constraint.startswith("<="):
        required = parse_version(constraint[2:].strip())
        return actual_v <= required
    if constraint.startswith(">"):
        required = parse_version(constraint[1:].strip())
        return actual_v > required
    if constraint.startswith("<"):
        required = parse_version(constraint[1:].strip())
        return actual_v < required
    if constraint.startswith("=="):
        required = parse_version(constraint[2:].strip())
        return actual_v == required
    if constraint.startswith("~"):
        required = parse_version(constraint[1:].strip())
        return actual_v[0] == required[0] and actual_v[1] == required[1]
    if constraint == "*":
        return True
    required = parse_version(constraint)
    return actual_v == required


def build_dependency_graph(records: dict[str, PluginRecord]) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = {}
    for plugin_id, record in records.items():
        deps = [d.plugin_id for d in record.manifest.required_dependencies]
        graph[plugin_id] = deps
    return graph


def detect_cycles(graph: dict[str, list[str]]) -> list[str]:
    visited: set[str] = set()
    stack: set[str] = set()
    cycle_path: list[str] = []

    def dfs(node: str, path: list[str]) -> bool:
        if node in stack:
            cycle_path.extend(path[path.index(node) :] + [node])
            return True
        if node in visited:
            return False
        visited.add(node)
        stack.add(node)
        for dep in graph.get(node, []):
            if dfs(dep, path + [node]):
                return True
        stack.remove(node)
        return False

    for node in graph:
        if dfs(node, []):
            return cycle_path
    return []


def resolve_install_order(
    plugin_id: str,
    records: dict[str, PluginRecord],
) -> list[str]:
    graph = build_dependency_graph(records)
    if plugin_id not in records:
        raise PluginNotFoundError(plugin_id)

    cycle = detect_cycles({**graph, plugin_id: graph.get(plugin_id, [])})
    if cycle:
        raise PluginCycleError(f"Dependency cycle detected: {' -> '.join(cycle)}")

    order: list[str] = []
    seen: set[str] = set()

    def visit(node: str) -> None:
        if node in seen:
            return
        for dep in graph.get(node, []):
            if dep not in records:
                raise PluginDependencyError(f"Missing required dependency: {dep}")
            visit(dep)
        seen.add(node)
        order.append(node)

    visit(plugin_id)
    return order


def check_dependencies(
    record: PluginRecord,
    installed: dict[str, PluginRecord],
) -> list[str]:
    """Return list of unmet required dependency ids."""
    missing: list[str] = []
    for dep in record.manifest.required_dependencies:
        other = installed.get(dep.plugin_id)
        if other is None or other.state not in (
            PluginState.INSTALLED,
            PluginState.ENABLED,
            PluginState.DISABLED,
        ):
            if other is None:
                missing.append(dep.plugin_id)
                continue
        if other and not version_satisfies(other.manifest.version, dep.version):
            raise PluginDependencyError(
                f"Plugin {record.id} requires {dep.plugin_id} {dep.version}, "
                f"found {other.manifest.version}"
            )
    return missing


def dependency_graph_payload(records: dict[str, PluginRecord]) -> dict[str, object]:
    graph = build_dependency_graph(records)
    cycles = detect_cycles(graph)
    return {
        "nodes": [
            {
                "id": pid,
                "version": rec.manifest.version,
                "state": rec.state.value,
            }
            for pid, rec in records.items()
        ],
        "edges": [
            {"from": pid, "to": dep, "type": "required"}
            for pid, deps in graph.items()
            for dep in deps
        ],
        "cycles": cycles,
        "valid": not cycles,
    }
