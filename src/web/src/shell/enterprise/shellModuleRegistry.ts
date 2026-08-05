/**
 * Shell Module Registry — Sprint 28.5 / clarified 35.1.
 * Dynamic UI projection over ENTERPRISE_MODULES + Desktop + Production.
 * NOT a platform navigation SoR — Platform Registry MENU_CATALOG is canonical.
 * Does NOT replace workspace/managers/moduleRegistry — bridges to shell nav.
 */

import { ENTERPRISE_MODULES, type EnterpriseModuleDef } from "@/modules/moduleCatalog";
import type { ShellIconId, ShellNavItem } from "./enterpriseNav";
import { MODULE_LABEL_RU } from "@/navigation/enterpriseRuNav";

export const SHELL_MODULE_REGISTRY_VERSION = "28.5";

export type ShellModuleCategory =
  | "core"
  | "business"
  | "ai"
  | "ops"
  | "platform"
  | "system";

export type ShellModuleRecord = {
  id: string;
  label: string;
  route: string;
  icon: ShellIconId | string;
  category: ShellModuleCategory;
  description?: string;
  badge?: string;
  comingSoon?: boolean;
  keywords: string[];
  source: "catalog" | "desktop" | "dynamic";
};

type Listener = () => void;
const listeners = new Set<Listener>();
const dynamicModules = new Map<string, ShellModuleRecord>();

function emit() {
  listeners.forEach((l) => l());
}

function categoryFor(id: string): ShellModuleCategory {
  if (["dashboard", "desktop", "city", "settings"].includes(id)) return "core";
  if (["crm", "erp", "projects", "documents", "knowledge"].includes(id)) return "business";
  if (["ai_studio", "ai_agents", "production", "production_studio"].includes(id)) return "ai";
  if (["analytics", "automation", "marketplace"].includes(id)) return "ops";
  if (["integrations", "security"].includes(id)) return "platform";
  return "system";
}

function fromCatalog(m: EnterpriseModuleDef): ShellModuleRecord {
  return {
    id: m.id,
    label: MODULE_LABEL_RU[m.id] || m.label,
    route: m.route,
    icon: m.icon,
    category: categoryFor(m.id),
    description: m.description,
    comingSoon: m.readiness === "coming_soon",
    keywords: [m.id, m.slug, m.label.toLowerCase(), ...(m.aliases || [])],
    source: "catalog",
  };
}

/** Desktop is not in ENTERPRISE_MODULES — inject for shell nav / search. */
const EXTRA: ShellModuleRecord[] = [
  {
    id: "desktop",
    label: MODULE_LABEL_RU.desktop || "Рабочий стол",
    route: "/desktop",
    icon: "desktop",
    category: "core",
    description: "Корпоративный рабочий стол",
    keywords: ["desktop", "os", "windows", "wm", "рабочий", "стол"],
    source: "desktop",
  },
];

function baseModules(): ShellModuleRecord[] {
  const fromCat = ENTERPRISE_MODULES.map(fromCatalog);
  const ids = new Set(fromCat.map((m) => m.id));
  const extras = EXTRA.filter((e) => !ids.has(e.id));
  return [...fromCat, ...extras];
}

export const shellModuleRegistry = {
  version: SHELL_MODULE_REGISTRY_VERSION,

  subscribe(listener: Listener) {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  },

  /** Register or replace a shell module (future modules auto-appear in nav/search). */
  register(module: ShellModuleRecord) {
    dynamicModules.set(module.id, { ...module, source: "dynamic" });
    emit();
    return module;
  },

  unregister(id: string) {
    dynamicModules.delete(id);
    emit();
  },

  get(id: string): ShellModuleRecord | undefined {
    return dynamicModules.get(id) || baseModules().find((m) => m.id === id);
  },

  list(): ShellModuleRecord[] {
    const map = new Map<string, ShellModuleRecord>();
    for (const m of baseModules()) map.set(m.id, m);
    for (const m of dynamicModules.values()) map.set(m.id, m);
    return [...map.values()];
  },

  byCategory(category: ShellModuleCategory): ShellModuleRecord[] {
    return this.list().filter((m) => m.category === category);
  },

  toNavItems(): ShellNavItem[] {
    const preferred = [
      "dashboard",
      "desktop",
      "city",
      "crm",
      "erp",
      "projects",
      "ai_studio",
      "production_studio",
      "ai_agents",
      "knowledge",
      "documents",
      "analytics",
      "marketplace",
      "automation",
      "integrations",
      "security",
      "settings",
    ];
    const all = this.list();
    const ordered: ShellModuleRecord[] = [];
    for (const id of preferred) {
      const hit = all.find((m) => m.id === id);
      if (hit) ordered.push(hit);
    }
    for (const m of all) {
      if (!ordered.some((o) => o.id === m.id)) ordered.push(m);
    }
    return ordered.map((m) => ({
      id: m.id,
      label: MODULE_LABEL_RU[m.id] || m.label,
      route: m.route,
      icon: (m.icon as ShellIconId) || "dashboard",
      badge: m.badge,
      comingSoon: m.comingSoon,
    }));
  },

  searchDocs() {
    return this.list().map((m) => ({
      id: `shell_mod_${m.id}`,
      category: "modules" as const,
      title: m.label,
      path: m.route,
      tokens: [...m.keywords, m.category, "module", "shell"],
      rankBoost: 15,
    }));
  },
};
