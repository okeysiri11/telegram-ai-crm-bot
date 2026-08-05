/**
 * Runtime dependency graph — Sprint 29.8.
 * Read-only topology. Circular dependencies are rejected.
 */

import type { DependencyEdge, RuntimeId } from "./orchestratorTypes";
import { runtimeRegistry } from "./RuntimeRegistry";

export class CircularDependencyError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "CircularDependencyError";
  }
}

function buildAdj(): Map<RuntimeId, RuntimeId[]> {
  const adj = new Map<RuntimeId, RuntimeId[]>();
  for (const a of runtimeRegistry.list()) {
    adj.set(a.id, [...a.dependencies]);
  }
  return adj;
}

/** Detect cycle via DFS. Throws if circular. */
export function assertAcyclic(adj?: Map<RuntimeId, RuntimeId[]>) {
  const graph = adj || buildAdj();
  const visiting = new Set<RuntimeId>();
  const visited = new Set<RuntimeId>();

  function dfs(node: RuntimeId, stack: RuntimeId[]) {
    if (visiting.has(node)) {
      throw new CircularDependencyError(
        `Circular dependency: ${[...stack, node].join(" → ")}`,
      );
    }
    if (visited.has(node)) return;
    visiting.add(node);
    for (const dep of graph.get(node) || []) {
      dfs(dep, [...stack, node]);
    }
    visiting.delete(node);
    visited.add(node);
  }

  for (const id of graph.keys()) {
    dfs(id, []);
  }
}

/** Topological order: dependencies before dependents */
export function topologicalOrder(): RuntimeId[] {
  const adj = buildAdj();
  assertAcyclic(adj);

  const indegree = new Map<RuntimeId, number>();
  for (const id of adj.keys()) indegree.set(id, 0);
  for (const [id, deps] of adj) {
    void id;
    for (const d of deps) {
      if (!indegree.has(d)) indegree.set(d, 0);
    }
  }
  // edge: dependency → runtime (dep must start first)
  // adapter.dependencies are prerequisites of adapter.id
  const dependents = new Map<RuntimeId, RuntimeId[]>();
  for (const id of adj.keys()) dependents.set(id, []);
  for (const [id, deps] of adj) {
    for (const d of deps) {
      if (!dependents.has(d)) dependents.set(d, []);
      dependents.get(d)!.push(id);
      indegree.set(id, (indegree.get(id) || 0) + 1);
      if (!indegree.has(d)) indegree.set(d, indegree.get(d) || 0);
    }
  }

  const queue = [...indegree.entries()].filter(([, n]) => n === 0).map(([id]) => id);
  const order: RuntimeId[] = [];
  while (queue.length) {
    const id = queue.shift()!;
    order.push(id);
    for (const next of dependents.get(id) || []) {
      const n = (indegree.get(next) || 0) - 1;
      indegree.set(next, n);
      if (n === 0) queue.push(next);
    }
  }

  if (order.length < indegree.size) {
    throw new CircularDependencyError("Circular dependency detected during topological sort");
  }
  return order;
}

export const runtimeDependencyGraph = {
  /** Read-only edges: from prerequisite → dependent */
  edges(): DependencyEdge[] {
    const edges: DependencyEdge[] = [];
    for (const a of runtimeRegistry.list()) {
      for (const dep of a.dependencies) {
        edges.push({ from: dep, to: a.id });
      }
    }
    return edges;
  },

  prerequisites(id: RuntimeId): RuntimeId[] {
    return [...(runtimeRegistry.get(id)?.dependencies || [])];
  },

  dependents(id: RuntimeId): RuntimeId[] {
    return runtimeRegistry.list().filter((a) => a.dependencies.includes(id)).map((a) => a.id);
  },

  order: topologicalOrder,
  assertAcyclic: () => assertAcyclic(),

  /** Canonical platform chain for docs/UI */
  canonicalChain(): RuntimeId[] {
    return [
      "business_network",
      "digital_citizen",
      "asset",
      "life",
      "spatial",
      "city_visualization",
      "interaction",
      "intelligence",
    ];
  },
};
