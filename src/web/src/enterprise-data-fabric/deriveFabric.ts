/**
 * Enterprise Data Fabric derivation — Sprint 33.3.
 * Pure client graph over live-ops / EI / Workflows / Integrations / Runtime.
 * No new Database Engine / Knowledge Engine / Store.
 */

import type { LiveEnterpriseSnapshot } from "@/live-ops";
import type { AppNotification } from "@/notifications/notificationStore";
import { BUSINESS_WORKFLOW_TEMPLATES } from "@/enterprise-workflow/workflowTemplates";
import { deriveIntelligence } from "@/enterprise-intelligence/deriveIntelligence";
import { deriveIntegrationHub } from "@/enterprise-integrations/deriveIntegrations";
import { deriveRuntime } from "@/ai-runtime/deriveRuntime";
import {
  FABRIC_EDGES,
  FABRIC_ENTITIES,
  KNOWLEDGE_CHAIN,
  getFabricEntity,
  type FabricEdge,
  type FabricEntity,
} from "./fabricCatalog";

export type FabricLineage = {
  entityId: string;
  source: string;
  changedBy: string;
  changedAt: string;
  workflow: string;
  aiParticipant: string;
};

export type FabricImpact = {
  entityId: string;
  dependsOn: string[];
  workflowsAffected: string[];
  aiUsing: string[];
  integrationsReceiving: string[];
};

export type FabricExplorer = {
  related: FabricEntity[];
  changeHistory: FabricLineage[];
  activeProcesses: string[];
  aiUsing: string[];
};

export type FabricExecutive = {
  linkedObjects: number;
  activeDependencies: number;
  problemLinks: number;
  missingData: number;
  recentChanges: string[];
};

export type FabricBundle = {
  entities: FabricEntity[];
  edges: FabricEdge[];
  knowledgeChain: typeof KNOWLEDGE_CHAIN;
  lineage: Record<string, FabricLineage>;
  impact: Record<string, FabricImpact>;
  executive: FabricExecutive;
  explore: (id: string) => FabricExplorer;
};

function hash(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

function neighbors(id: string): string[] {
  const out: string[] = [];
  for (const e of FABRIC_EDGES) {
    if (e.from === id) out.push(e.to);
    if (e.to === id) out.push(e.from);
  }
  return [...new Set(out)];
}

export function deriveDataFabric(
  snapshot: LiveEnterpriseSnapshot,
  opts: {
    company?: string;
    notifications?: AppNotification[];
    roleId?: string;
  } = {},
): FabricBundle {
  const notifications = opts.notifications || [];
  const intel = deriveIntelligence(snapshot, notifications);
  const intHub = deriveIntegrationHub(snapshot);
  const runtime = deriveRuntime(snapshot, notifications);
  const wfTitles = BUSINESS_WORKFLOW_TEMPLATES.map((w) => w.title);
  const company = opts.company || "Enterprise";

  const activityBlob = snapshot.activity.map((a) => `${a.title} ${a.kind}`).join(" ").toLowerCase();
  const healthIds = new Set(snapshot.health.filter((h) => !h.ok).map((h) => h.id));

  const entities: FabricEntity[] = FABRIC_ENTITIES.map((e) => {
    const copy = { ...e };
    if (e.id === "company") copy.detail = company;
    if (e.id === "ai_team") {
      copy.detail = `${snapshot.aiOps.running.length} active · Q ${snapshot.aiOps.queue.length}`;
      copy.problem = snapshot.aiOps.errors.length > 0;
    }
    if (e.id === "clients" || e.id === "deals") {
      const hit = /crm|client|deal|сделк|клиент/.test(activityBlob) || snapshot.activeModules.includes("crm");
      copy.missing = !hit && !snapshot.health.some((h) => h.id === "crm" && h.ok);
      copy.problem = healthIds.has("crm");
    }
    if (e.id === "documents") {
      copy.problem = healthIds.has("documents");
      copy.missing = !/doc|документ/.test(activityBlob) && !snapshot.activeModules.some((m) => /doc/.test(m));
    }
    if (e.id === "knowledge") {
      copy.problem = healthIds.has("knowledge");
      copy.missing = !intel.knowledgeAware;
      copy.detail = intel.knowledgeAware ? "KB aware" : "weak signals";
    }
    if (e.id === "workflows") {
      copy.detail = `${wfTitles.length} templates · ${runtime.counts.active} running`;
    }
    if (e.id === "integrations") {
      copy.detail = `${intHub.dashboard.active} active`;
      copy.problem = intHub.dashboard.errors > 0;
      copy.missing = intHub.dashboard.needsSetup > 3;
    }
    if (e.id === "users") {
      copy.detail = opts.roleId || "roles";
    }
    return copy;
  });

  // Soft edges from EI cross-module
  const edges: FabricEdge[] = [...FABRIC_EDGES];
  for (const link of intel.crossModule.slice(0, 4)) {
    const from =
      /crm|client|deal/i.test(link.from) ? "deals" : /knowledge/i.test(link.from) ? "knowledge" : /doc/i.test(link.from) ? "documents" : null;
    const to =
      /finance|crm/i.test(link.to) ? "clients" : /legal|knowledge/i.test(link.to) ? "knowledge" : /workflow/i.test(link.to) ? "workflows" : null;
    if (from && to && !edges.some((e) => e.from === from && e.to === to && e.label === link.title)) {
      edges.push({ id: `dyn_${link.id}`, from, to, label: link.title });
    }
  }

  const lineage: Record<string, FabricLineage> = {};
  const actors = ["Owner", "Ops Manager", "Concierge", opts.roleId || "User", "System"];
  const sources = ["CRM sync", "Knowledge Base", "Workflow run", "Integration Hub", "User edit", "AI Team"];

  for (const e of entities) {
    const act = snapshot.activity[hash(e.id) % Math.max(snapshot.activity.length, 1)];
    lineage[e.id] = {
      entityId: e.id,
      source: sources[hash(e.id) % sources.length]!,
      changedBy: actors[hash(e.label) % actors.length]!,
      changedAt: act?.at || snapshot.updatedAt,
      workflow: wfTitles[hash(e.id) % Math.max(wfTitles.length, 1)] || "—",
      aiParticipant:
        snapshot.aiOps.running[hash(e.id) % Math.max(snapshot.aiOps.running.length, 1)] ||
        snapshot.aiOps.recent[0] ||
        "Concierge",
    };
  }

  const impact: Record<string, FabricImpact> = {};
  for (const e of entities) {
    const deps = neighbors(e.id)
      .map((id) => getFabricEntity(id)?.label || id)
      .filter(Boolean);
    impact[e.id] = {
      entityId: e.id,
      dependsOn: deps,
      workflowsAffected: wfTitles.filter((_, i) => hash(e.id + i) % 3 === 0).slice(0, 3),
      aiUsing: [
        ...new Set(
          [
            ...snapshot.aiOps.running.slice(0, 2),
            lineage[e.id]?.aiParticipant,
            e.kind === "ai" ? "Concierge" : "Ops Copilot",
          ].filter(Boolean) as string[],
        ),
      ].slice(0, 4),
      integrationsReceiving: intHub.twin.connectedSystems.slice(0, 4),
    };
  }

  const problemLinks = edges.filter((edge) => {
    const a = entities.find((x) => x.id === edge.from);
    const b = entities.find((x) => x.id === edge.to);
    return a?.problem || b?.problem || a?.missing || b?.missing;
  }).length;

  const executive: FabricExecutive = {
    linkedObjects: entities.length + edges.length,
    activeDependencies: edges.length + runtime.counts.active,
    problemLinks,
    missingData: entities.filter((e) => e.missing).length,
    recentChanges: snapshot.activity.slice(0, 5).map((a) => a.title),
  };

  function explore(id: string): FabricExplorer {
    const relatedIds = neighbors(id);
    // twin virtual neighbor for knowledge chain
    const related = relatedIds
      .map((rid) => entities.find((e) => e.id === rid))
      .filter(Boolean) as FabricEntity[];
    if (id === "knowledge" || id === "ai_team") {
      related.push({
        id: "twin",
        kind: "company",
        label: "Digital Twin",
        detail: "Organization mirror",
        route: "/enterprise-twin",
      });
    }
    const history = [lineage[id], ...relatedIds.slice(0, 2).map((rid) => lineage[rid])].filter(
      Boolean,
    ) as FabricLineage[];
    return {
      related,
      changeHistory: history,
      activeProcesses: runtime.twin.processesRunning.slice(0, 4),
      aiUsing: impact[id]?.aiUsing || [],
    };
  }

  return {
    entities,
    edges,
    knowledgeChain: KNOWLEDGE_CHAIN,
    lineage,
    impact,
    executive,
    explore,
  };
}
