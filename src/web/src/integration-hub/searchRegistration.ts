/**
 * Universal search registration — Sprint 28.0.
 * Extends searchIndex with OS surfaces + production + city. Idempotent.
 */

import { searchIndex } from "../../navigation/managers/searchIndex";
import { registerUnifiedWorkspaceSearch } from "@/workspace-chrome/registerUnifiedSearch";
import { CITY_BUILDINGS } from "@/enterprise-city/cityCatalog";
import { PRODUCTION_STUDIOS } from "@/ai-production-studio/productionCatalog";
import { OS_DEEP_LINKS } from "./types";
import { listActivity } from "@/workspace-engine/activityJournal";

let registered = false;

export function registerIntegrationSearch() {
  registerUnifiedWorkspaceSearch();
  if (registered) return;
  registered = true;

  for (const link of OS_DEEP_LINKS) {
    searchIndex.upsert({
      id: `hub_${link.id}`,
      category: "modules",
      title: link.label,
      path: link.path,
      tokens: [...link.tokens, "os", "hub", "navigate"],
      rankBoost: 14,
    });
  }

  for (const b of CITY_BUILDINGS) {
    searchIndex.upsert({
      id: `hub_city_${b.id}`,
      category: "modules",
      title: `City · ${b.label}`,
      path: b.route.startsWith("/enterprise-city")
        ? `/enterprise-city?building=${b.id}`
        : b.route,
      tokens: [...b.searchTokens, "city", "building", b.district],
      rankBoost: 9,
    });
  }

  for (const s of PRODUCTION_STUDIOS) {
    searchIndex.upsert({
      id: `hub_prod_${s.id}`,
      category: "applications",
      title: `Production · ${s.label}`,
      path: `/production-studio?studio=${s.id}`,
      tokens: [s.id, s.label.toLowerCase(), "production", "studio", ...s.aiAgents.map((a) => a.toLowerCase())],
      rankBoost: 10,
    });
  }

  searchIndex.upsert({
    id: "hub_crm_projects",
    category: "crm",
    title: "CRM · Projects & pipeline",
    path: "/crm",
    tokens: ["crm", "projects", "pipeline", "clients"],
    rankBoost: 11,
  });

  searchIndex.upsert({
    id: "hub_settings",
    category: "modules",
    title: "Settings · Workspace & theme",
    path: "/settings",
    tokens: ["settings", "theme", "locale", "workspace"],
    rankBoost: 8,
  });

  try {
    for (const a of listActivity().slice(0, 12)) {
      searchIndex.upsert({
        id: `hub_act_${a.id}`,
        category: "commands",
        title: `Recent · ${a.title}`,
        path: "/dashboard",
        tokens: ["recent", "activity", a.kind, a.title.toLowerCase()],
        rankBoost: 5,
      });
    }
  } catch {
    /* journal optional */
  }
}
