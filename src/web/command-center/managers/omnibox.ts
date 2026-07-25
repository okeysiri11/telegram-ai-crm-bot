import type { SearchHit } from "../types";
import { fuzzyScore } from "./fuzzy";

type IndexEntry = {
  id: string;
  type: string;
  title: string;
  route: string;
  keywords: string[];
};

const INDEX: IndexEntry[] = [
  { id: "app_ws", type: "applications", title: "Workspace", route: "/workspace", keywords: ["workspace", "home"] },
  { id: "app_cc", type: "applications", title: "Command Center", route: "/command-center", keywords: ["command", "productivity"] },
  { id: "app_id", type: "applications", title: "Identity Center", route: "/identity", keywords: ["identity", "rbac"] },
  { id: "app_nav", type: "applications", title: "Navigation", route: "/navigation", keywords: ["navigation"] },
  { id: "mod_crm", type: "modules", title: "CRM", route: "/workspace/crm", keywords: ["crm", "leads"] },
  { id: "mod_erp", type: "modules", title: "ERP", route: "/workspace/erp", keywords: ["erp", "inventory"] },
  { id: "mod_ai", type: "modules", title: "AI Studio", route: "/workspace/ai", keywords: ["ai", "studio"] },
  { id: "mod_mkt", type: "marketplace", title: "Marketplace", route: "/workspace/marketplace", keywords: ["marketplace"] },
  { id: "mod_beauty", type: "modules", title: "Beauty OS", route: "/workspace/beauty", keywords: ["beauty"] },
  { id: "vert_auto", type: "verticals", title: "Auto Vertical", route: "/workspace/auto", keywords: ["auto"] },
  { id: "vert_agro", type: "verticals", title: "Agro Vertical", route: "/workspace/agro", keywords: ["agro"] },
  { id: "dash_main", type: "dashboards", title: "Personal Dashboard", route: "/workspace/dashboards", keywords: ["dashboard"] },
  { id: "rep_weekly", type: "reports", title: "Weekly KPI Report", route: "/workspace/reports/weekly", keywords: ["report", "weekly"] },
  { id: "an_main", type: "analytics", title: "Analytics", route: "/workspace/analytics", keywords: ["analytics"] },
  { id: "set_main", type: "settings", title: "Settings", route: "/settings", keywords: ["settings"] },
  { id: "kb_sec", type: "knowledge", title: "Security Policy", route: "/workspace/docs/security", keywords: ["knowledge", "security"] },
  { id: "wf_inv", type: "workflows", title: "Invoice Approval", route: "/workspace/workflows/invoice", keywords: ["workflow"] },
  { id: "agent_ops", type: "ai_agents", title: "Ops Copilot", route: "/workspace/ai", keywords: ["agent", "copilot"] },
  { id: "crm_acme", type: "crm", title: "Client Acme Corp", route: "/workspace/crm?client=acme", keywords: ["client", "acme"] },
  { id: "erp_sku", type: "erp", title: "SKU-1042 Brake Pad", route: "/workspace/erp?sku=1042", keywords: ["sku"] },
  { id: "usr_alex", type: "users", title: "Alex Owner", route: "/identity/users", keywords: ["user", "alex"] },
  { id: "org_demo", type: "organizations", title: "Demo Corp", route: "/identity/organizations", keywords: ["org"] },
  { id: "doc_brief", type: "documents", title: "Q3 Brief", route: "/workspace/docs/q3", keywords: ["document"] },
  { id: "prj_web", type: "projects", title: "Enterprise Web", route: "/workspace/list", keywords: ["project"] },
  { id: "task_mig", type: "tasks", title: "Review Migration", route: "/workspace?task=migration", keywords: ["task"] },
];

const usage = new Map<string, number>();
const recentIds: string[] = [];
const favorites = new Set(["mod_crm", "app_ws", "act_create_task"]);

export const navigationIndex = {
  list(): IndexEntry[] {
    return [...INDEX];
  },
  recordUse(id: string) {
    usage.set(id, (usage.get(id) ?? 0) + 1);
    recentIds.push(id);
    if (recentIds.length > 50) recentIds.shift();
  },
};

export const omniboxEngine = {
  search(query: string, limit = 20): SearchHit[] {
    const q = query.trim();
    const hits: SearchHit[] = [];
    for (const entry of INDEX) {
      const hay = [entry.title, entry.type, ...entry.keywords].join(" ");
      const relevance = q ? fuzzyScore(q, hay) : 0.4;
      if (q && relevance < 0.25) continue;
      const frequency = usage.get(entry.id) ?? 0;
      const recency = recentIds.slice(-10).includes(entry.id) ? 1 : 0;
      const fav = favorites.has(entry.id) ? 1 : 0;
      const aiConfidence = Math.min(1, relevance + 0.05);
      const score =
        relevance * 0.4 +
        recency * 0.15 +
        Math.min(frequency, 10) / 10 * 0.15 +
        fav * 0.1 +
        aiConfidence * 0.1 +
        0.1;
      hits.push({
        id: entry.id,
        title: entry.title,
        type: entry.type,
        route: entry.route,
        score: Math.round(score * 10000) / 10000,
        signals: {
          relevance,
          recency,
          frequency,
          permissions: true,
          workspace: "default",
          organization: "demo_corp",
          ai_confidence: aiConfidence,
        },
      });
    }
    hits.sort((a, b) => b.score - a.score);
    return hits.slice(0, limit);
  },
};
