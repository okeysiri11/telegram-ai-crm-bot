/**
 * Shell search refresh — Sprint 28.5.
 * Projects module registry + production assets into existing searchIndex.
 */

import { searchIndex } from "../../../navigation/managers/searchIndex";
import { useProductionStore } from "@/ai-production-studio/productionStore";
import { shellModuleRegistry } from "./shellModuleRegistry";

export function refreshShellSearch() {
  for (const doc of shellModuleRegistry.searchDocs()) {
    searchIndex.upsert(doc);
  }

  try {
    const state = useProductionStore.getState();
    for (const p of state.projects || []) {
      const title = p.title || p.id;
      searchIndex.upsert({
        id: `shell_prod_project_${p.id}`,
        category: "projects",
        title,
        path: `/production-studio?project=${encodeURIComponent(p.id)}`,
        tokens: ["production", "project", "asset", title.toLowerCase()],
        rankBoost: 8,
      });
    }
    for (const pr of (state.prompts || []).slice(0, 40)) {
      const title = pr.title || pr.id;
      searchIndex.upsert({
        id: `shell_prod_prompt_${pr.id}`,
        category: "knowledge",
        title: `Prompt · ${title}`,
        path: `/production-studio?tab=prompts&prompt=${encodeURIComponent(pr.id)}`,
        tokens: ["prompt", "production", "asset", title.toLowerCase()],
        rankBoost: 6,
      });
    }
    for (const g of (state.generations || []).slice(0, 24)) {
      const title = g.title || g.id;
      searchIndex.upsert({
        id: `shell_prod_gen_${g.id}`,
        category: "applications",
        title: `Generation · ${title}`,
        path: `/ai-studio?generation=${encodeURIComponent(g.id)}`,
        tokens: ["generation", "production", "asset", title.toLowerCase()],
        rankBoost: 5,
      });
    }
  } catch {
    /* production store optional during early boot */
  }

  searchIndex.upsert({
    id: "shell_settings_runtime",
    category: "modules",
    title: "Settings · Runtime",
    path: "/settings",
    tokens: ["settings", "runtime", "theme", "session"],
    rankBoost: 10,
  });
}
