"""Service dependency graph resolver — startup/shutdown order, cycles, missing."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import TYPE_CHECKING

from platform_service_builder.models import DependencyNode, ServiceState

if TYPE_CHECKING:
    from platform_service_builder.models import ServiceDefinition


class ServiceDependencyResolver:
    def __init__(self) -> None:
        self._edges: dict[str, list[str]] = defaultdict(list)

    def reset(self) -> None:
        self._edges.clear()

    def set_dependencies(self, service_id: str, dependencies: list[str]) -> None:
        self._edges[service_id] = list(dependencies)

    def remove(self, service_id: str) -> None:
        self._edges.pop(service_id, None)
        for deps in self._edges.values():
            while service_id in deps:
                deps.remove(service_id)

    def dependencies_of(self, service_id: str) -> list[str]:
        return list(self._edges.get(service_id, []))

    def dependents_of(self, service_id: str) -> list[str]:
        return [sid for sid, deps in self._edges.items() if service_id in deps]

    def detect_cycles(self) -> list[list[str]]:
        """Return list of cycles (each cycle as ordered service ids)."""
        cycles: list[list[str]] = []
        visiting: set[str] = set()
        visited: set[str] = set()
        stack: list[str] = []

        def dfs(node: str) -> None:
            if node in visiting:
                if node in stack:
                    idx = stack.index(node)
                    cycles.append(stack[idx:] + [node])
                return
            if node in visited:
                return
            visiting.add(node)
            stack.append(node)
            for dep in self._edges.get(node, []):
                dfs(dep)
            stack.pop()
            visiting.remove(node)
            visited.add(node)

        for sid in list(self._edges.keys()):
            dfs(sid)
        return cycles

    def has_cycle_involving(self, service_id: str) -> bool:
        return any(service_id in c for c in self.detect_cycles())

    def resolve_startup_order(self, service_ids: list[str] | None = None) -> list[str]:
        """Kahn topological sort — dependencies first."""
        nodes = set(service_ids) if service_ids is not None else set(self._edges.keys())
        for sid in list(nodes):
            nodes.update(self._edges.get(sid, []))

        indegree: dict[str, int] = {n: 0 for n in nodes}
        reverse: dict[str, list[str]] = defaultdict(list)
        for sid in nodes:
            for dep in self._edges.get(sid, []):
                if dep not in nodes:
                    continue
                # edge dep -> sid (dep must start before sid)
                reverse[dep].append(sid)
                indegree[sid] = indegree.get(sid, 0) + 1
                indegree.setdefault(dep, indegree.get(dep, 0))

        queue = deque(sorted(n for n, d in indegree.items() if d == 0))
        order: list[str] = []
        while queue:
            n = queue.popleft()
            order.append(n)
            for child in reverse.get(n, []):
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)

        if len(order) != len(nodes):
            # cyclic — return best-effort remaining appended
            remaining = sorted(nodes - set(order))
            order.extend(remaining)
        return order

    def resolve_shutdown_order(self, service_ids: list[str] | None = None) -> list[str]:
        return list(reversed(self.resolve_startup_order(service_ids)))

    def graph(
        self,
        service_id: str,
        *,
        definitions: dict[str, ServiceDefinition],
        _seen: set[str] | None = None,
        _path: list[str] | None = None,
    ) -> DependencyNode:
        seen = _seen if _seen is not None else set()
        path = _path if _path is not None else []

        if service_id in path:
            return DependencyNode(service_id=service_id, status="cyclic", state=None, children=[])

        defn = definitions.get(service_id)
        if defn is None:
            return DependencyNode(service_id=service_id, status="missing", state=None, children=[])

        if not defn.enabled or defn.state == ServiceState.DISABLED:
            status = "disabled"
        elif defn.state == ServiceState.FAILED:
            status = "failed"
        elif defn.state in {ServiceState.RUNNING, ServiceState.LOADED, ServiceState.PAUSED}:
            status = "healthy"
        else:
            status = "installed" if defn.state == ServiceState.INSTALLED else defn.state.value

        if service_id in seen:
            return DependencyNode(
                service_id=service_id,
                status=status,
                state=defn.state.value,
                children=[],
            )

        seen.add(service_id)
        children = [
            self.graph(dep, definitions=definitions, _seen=seen, _path=path + [service_id])
            for dep in self._edges.get(service_id, [])
        ]
        return DependencyNode(
            service_id=service_id,
            status=status,
            state=defn.state.value,
            children=children,
        )

    def missing_dependencies(self, service_id: str, known: set[str]) -> list[str]:
        return [d for d in self._edges.get(service_id, []) if d not in known]


dependency_resolver = ServiceDependencyResolver()
