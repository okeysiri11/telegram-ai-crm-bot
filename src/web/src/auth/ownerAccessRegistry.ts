/**
 * Owner access smoke matrix — derived from existing route/workspace catalogs.
 * Do not maintain a fragile one-off list for every module.
 */

import { INTEGRATION_ROUTES } from "@/platform-integration/platformBoot";
import { LAUNCH_CRITICAL_ROUTES, LAUNCH_DEMO_STEPS } from "@/launch/launchCatalog";
import { VERTICAL_WORKSPACES } from "@/vertical-workspace/catalog";
import { MODULE_LANDINGS } from "@/modules/moduleLandingCatalog";
import { ROOM_CATALOG } from "@/casino/state/casinoRoutes";
import { isRouteAllowedForViewMode } from "@/ux-revolution/viewModeCatalog";

const AUTH_ONLY = new Set([
  "/login",
  "/logout",
  "/auth/logout",
  "/auth/register",
  "/auth/forgot-password",
  "/auth/access-denied",
  "/auth/unauthorized",
]);

/** Casino deep-links that must survive Owner returnTo. */
export const CASINO_OWNER_ROUTES = [
  "/casino",
  "/casino/lobby",
  "/casino/map",
  "/casino/roulette",
  "/casino/roulette/table/royale-1",
  "/casino/blackjack",
  "/casino/poker",
  "/casino/slots",
  "/casino/vip",
  "/casino/bar",
  "/casino/restaurant",
] as const;

function stripQuery(path: string): string {
  return path.split("?")[0]?.split("#")[0] || path;
}

function collectCatalogPaths(): string[] {
  const paths = new Set<string>();
  for (const route of INTEGRATION_ROUTES) paths.add(stripQuery(route.path));
  for (const route of LAUNCH_CRITICAL_ROUTES) paths.add(stripQuery(route));
  for (const step of LAUNCH_DEMO_STEPS) paths.add(stripQuery(step.route));
  for (const vertical of VERTICAL_WORKSPACES) {
    paths.add(stripQuery(vertical.route));
    if (vertical.legacyRoute) paths.add(stripQuery(vertical.legacyRoute));
  }
  for (const landing of MODULE_LANDINGS) paths.add(stripQuery(landing.route));
  for (const room of ROOM_CATALOG) paths.add(room.route);
  for (const casino of CASINO_OWNER_ROUTES) paths.add(casino);
  paths.add("/owner");
  paths.add("/dashboard");
  paths.add("/settings");
  paths.add("/command-center");
  paths.add("/creative-factory");
  paths.add("/workspace/crypto");
  paths.add("/workspace/beauty");
  paths.add("/workspace/cafe");
  paths.add("/workspace/agro");
  paths.add("/workspace/drone");
  paths.add("/workspace/legal");
  paths.add("/vertical/travel");
  return [...paths].filter((path) => path.startsWith("/") && !AUTH_ONLY.has(path)).sort();
}

export function ownerAccessSmokeRoutes(): string[] {
  return collectCatalogPaths();
}

export function ownerWorkspaceRoutes(): string[] {
  return collectCatalogPaths().filter((path) => path.startsWith("/workspace"));
}

export function ownerVerticalRoutes(): string[] {
  return collectCatalogPaths().filter((path) => path.startsWith("/vertical") || path.startsWith("/workspace/"));
}

export function assertOwnerRouteAccess(mode: "platform_owner" = "platform_owner"): {
  ok: boolean;
  denied: string[];
} {
  const denied = ownerAccessSmokeRoutes().filter((route) => !isRouteAllowedForViewMode(route, mode));
  return { ok: denied.length === 0, denied };
}
