/**
 * Register unified search docs — Sprint 32.3.6.
 * Extends existing searchIndex; no new search engine.
 */

import { searchIndex } from "../../navigation/managers/searchIndex";
import { moduleRegistry } from "../../workspace/managers/moduleRegistry";
import { GLOBAL_QUICK_SWITCH } from "./workspaceContext";

let registered = false;

export function registerUnifiedWorkspaceSearch() {
  if (registered) return;
  registered = true;

  for (const item of GLOBAL_QUICK_SWITCH) {
    searchIndex.upsert({
      id: `uws_${item.id}`,
      category: "modules",
      title: item.label,
      path: item.route,
      tokens: [item.label.toLowerCase(), item.hint.toLowerCase(), "workspace", "switch"],
      rankBoost: 11,
    });
  }

  for (const eco of moduleRegistry.ecosystems()) {
    const route = moduleRegistry.routeFor(eco);
    const meta = moduleRegistry.resolve(eco);
    searchIndex.upsert({
      id: `eco_${eco}`,
      category: "modules",
      title: `${meta.title || eco} Ecosystem`,
      path: route,
      tokens: [eco, "ecosystem", "workspace", meta.title?.toLowerCase() || eco],
      rankBoost: 9,
    });
  }

  searchIndex.upsert({
    id: "uws_users",
    category: "users",
    title: "Employees / Identity Users",
    path: "/identity/users",
    tokens: ["employees", "staff", "people", "users", "hr"],
    rankBoost: 7,
  });
  searchIndex.upsert({
    id: "uws_ai",
    category: "ai_agents",
    title: "AI Team Center",
    path: "/platform-builder/ai-team",
    tokens: ["ai", "agents", "team", "copilot"],
    rankBoost: 10,
  });
  searchIndex.upsert({
    id: "uws_docs",
    category: "documents",
    title: "Workspace Documents",
    path: "/workspace/docs",
    tokens: ["documents", "docs", "files"],
    rankBoost: 8,
  });
  searchIndex.upsert({
    id: "uws_workflows",
    category: "workflows",
    title: "Workflow Center",
    path: "/platform-builder/workflow-center",
    tokens: ["workflow", "automation", "processes", "wf"],
    rankBoost: 11,
  });
}
