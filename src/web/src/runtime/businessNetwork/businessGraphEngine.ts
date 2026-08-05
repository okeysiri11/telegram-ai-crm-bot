/**
 * Business Graph Engine — Sprint 29.0.
 * Relationship storage · traversal · queries · visualization-ready graph.
 */

import type {
  BusinessProfile,
  BusinessRelationship,
  GraphEdge,
  GraphNode,
  GraphQueryResult,
  RelationshipType,
} from "./ebnTypes";

function edgeWeight(type: RelationshipType, state: string): number {
  if (state !== "approved") return 0.2;
  const map: Record<RelationshipType, number> = {
    friend: 0.4,
    partner: 0.7,
    trusted_partner: 0.9,
    strategic_partner: 1,
    supplier: 0.65,
    client: 0.65,
    dealer: 0.55,
    contractor: 0.6,
    internal_organization: 0.85,
  };
  return map[type] ?? 0.5;
}

export const businessGraphEngine = {
  buildNodes(profiles: BusinessProfile[]): GraphNode[] {
    return profiles.map((p) => ({
      id: p.id,
      profileId: p.id,
      label: p.companyName,
      category: p.category,
      trustLevel: p.trustLevel,
    }));
  },

  buildEdges(relationships: BusinessRelationship[]): GraphEdge[] {
    return relationships
      .filter((r) => r.state !== "archived")
      .map((r) => ({
        id: `e_${r.id}`,
        relationshipId: r.id,
        from: r.fromProfileId,
        to: r.toProfileId,
        type: r.type,
        state: r.state,
        weight: edgeWeight(r.type, r.state),
      }));
  },

  /** Neighbors of a company (1-hop). */
  connections(
    profileId: string,
    profiles: BusinessProfile[],
    relationships: BusinessRelationship[],
  ): GraphQueryResult {
    const edges = this.buildEdges(relationships).filter(
      (e) => e.from === profileId || e.to === profileId,
    );
    const ids = new Set<string>([profileId]);
    for (const e of edges) {
      ids.add(e.from);
      ids.add(e.to);
    }
    const nodes = this.buildNodes(profiles.filter((p) => ids.has(p.id)));
    return { nodes, edges };
  },

  /** BFS traversal up to maxDepth hops. */
  traverse(
    startProfileId: string,
    profiles: BusinessProfile[],
    relationships: BusinessRelationship[],
    maxDepth = 2,
    approvedOnly = true,
  ): GraphQueryResult {
    const allEdges = this.buildEdges(relationships).filter((e) =>
      approvedOnly ? e.state === "approved" : true,
    );
    const adj = new Map<string, GraphEdge[]>();
    for (const e of allEdges) {
      if (!adj.has(e.from)) adj.set(e.from, []);
      if (!adj.has(e.to)) adj.set(e.to, []);
      adj.get(e.from)!.push(e);
      adj.get(e.to)!.push(e);
    }

    const visited = new Set<string>([startProfileId]);
    const usedEdges = new Set<string>();
    let frontier = [startProfileId];
    for (let d = 0; d < maxDepth; d++) {
      const next: string[] = [];
      for (const node of frontier) {
        for (const e of adj.get(node) || []) {
          usedEdges.add(e.id);
          const other = e.from === node ? e.to : e.from;
          if (!visited.has(other)) {
            visited.add(other);
            next.push(other);
          }
        }
      }
      frontier = next;
    }

    const nodes = this.buildNodes(profiles.filter((p) => visited.has(p.id)));
    const edges = allEdges.filter((e) => usedEdges.has(e.id));
    return { nodes, edges };
  },

  /** Shortest path between two profiles (unweighted BFS). */
  path(
    fromId: string,
    toId: string,
    relationships: BusinessRelationship[],
  ): GraphQueryResult {
    const edges = this.buildEdges(relationships).filter((e) => e.state === "approved");
    const adj = new Map<string, { peer: string; edge: GraphEdge }[]>();
    for (const e of edges) {
      if (!adj.has(e.from)) adj.set(e.from, []);
      if (!adj.has(e.to)) adj.set(e.to, []);
      adj.get(e.from)!.push({ peer: e.to, edge: e });
      adj.get(e.to)!.push({ peer: e.from, edge: e });
    }

    const prev = new Map<string, { peer: string; edge: GraphEdge }>();
    const q = [fromId];
    const seen = new Set([fromId]);
    let found = false;
    while (q.length) {
      const cur = q.shift()!;
      if (cur === toId) {
        found = true;
        break;
      }
      for (const link of adj.get(cur) || []) {
        if (seen.has(link.peer)) continue;
        seen.add(link.peer);
        prev.set(link.peer, { peer: cur, edge: link.edge });
        q.push(link.peer);
      }
    }
    if (!found) return { nodes: [], edges: [], path: [] };

    const pathIds: string[] = [toId];
    const pathEdges: GraphEdge[] = [];
    let walk = toId;
    while (walk !== fromId) {
      const step = prev.get(walk);
      if (!step) break;
      pathEdges.push(step.edge);
      walk = step.peer;
      pathIds.push(walk);
    }
    pathIds.reverse();
    return { nodes: [], edges: pathEdges.reverse(), path: pathIds };
  },

  /** Full graph snapshot for future visualization. */
  snapshot(profiles: BusinessProfile[], relationships: BusinessRelationship[]): GraphQueryResult {
    return {
      nodes: this.buildNodes(profiles),
      edges: this.buildEdges(relationships),
    };
  },
};
