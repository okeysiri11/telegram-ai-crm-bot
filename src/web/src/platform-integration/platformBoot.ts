/**
 * Sprint 30.6 — Platform boot: single coherent entry map for local launch.
 * Verifies canonical short routes + deep module routes. No parallel router.
 */

export const PLATFORM_BOOT_VERSION = "30.6";

export type BootRoute = {
  id: string;
  path: string;
  label: string;
  labelRu: string;
  required: boolean;
};

/** Application boot entry points (Home → Settings). */
export const BOOT_ENTRY_ROUTES: BootRoute[] = [
  { id: "home", path: "/", label: "Home", labelRu: "Главная", required: true },
  { id: "login", path: "/login", label: "Login", labelRu: "Вход", required: true },
  { id: "dashboard", path: "/dashboard", label: "Dashboard", labelRu: "Дашборд", required: true },
  { id: "city", path: "/city", label: "City", labelRu: "Город", required: true },
  { id: "ai", path: "/ai", label: "AI Center", labelRu: "AI-центр", required: true },
  { id: "production", path: "/production", label: "Production Studio", labelRu: "Продакшн", required: true },
  { id: "settings", path: "/settings", label: "Settings", labelRu: "Настройки", required: true },
];

/** Sprint-required route aliases / destinations. */
export const INTEGRATION_ROUTES: BootRoute[] = [
  ...BOOT_ENTRY_ROUTES,
  { id: "crm", path: "/crm", label: "CRM", labelRu: "CRM", required: true },
  { id: "erp", path: "/erp", label: "ERP", labelRu: "ERP", required: true },
  { id: "analytics", path: "/analytics", label: "Analytics", labelRu: "Аналитика", required: true },
  { id: "owner", path: "/owner", label: "Owner", labelRu: "Владелец", required: true },
  { id: "enterprise_city", path: "/enterprise-city", label: "Enterprise City", labelRu: "Город предприятия", required: true },
  { id: "ai_agents", path: "/ai-agents", label: "AI Agents", labelRu: "AI-Агенты", required: true },
  { id: "production_studio", path: "/production-studio", label: "Production Studio", labelRu: "Продакшн-студия", required: true },
  { id: "knowledge", path: "/knowledge", label: "Knowledge", labelRu: "Знания", required: true },
  { id: "health", path: "/health", label: "Platform Health", labelRu: "Здоровье платформы", required: true },
  { id: "demo", path: "/demo/scenario", label: "Live Demo", labelRu: "Живое демо", required: true },
];

/** Short path → canonical module path (aliases resolved in App.tsx). */
export const ROUTE_ALIASES: Record<string, string> = {
  "/ai": "/ai-agents",
  "/production": "/production-studio",
  "/city": "/city", // same page as enterprise-city
  "/login": "/login",
};

export function bootRouteIds(): string[] {
  return INTEGRATION_ROUTES.map((r) => r.id);
}

export function requiredBootPaths(): string[] {
  return INTEGRATION_ROUTES.filter((r) => r.required).map((r) => r.path);
}

export function assertBootCoverage(registeredPaths: string[]): { ok: boolean; missing: string[] } {
  const set = new Set(registeredPaths);
  const missing = requiredBootPaths().filter((p) => {
    if (set.has(p)) return false;
    // Alias targets count as covered when their destination is registered
    const aliasTarget = ROUTE_ALIASES[p];
    if (aliasTarget && set.has(aliasTarget)) return false;
    // /city and /enterprise-city are equivalent city surfaces
    if (p === "/city" && set.has("/enterprise-city")) return false;
    if (p === "/ai" && set.has("/ai-agents")) return false;
    if (p === "/production" && set.has("/production-studio")) return false;
    return true;
  });
  return { ok: missing.length === 0, missing };
}
