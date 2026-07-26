import type { RegisteredApplication } from "../types";
import { moduleRegistry } from "../../workspace/managers/moduleRegistry";

/**
 * Application launcher registry — Sprint 30.5.
 * Ecosystem apps are derived from moduleRegistry to avoid catalog drift.
 */

function fromModule(
  id: string,
  code: string,
  icon: string,
  owner: string,
): RegisteredApplication {
  const m = moduleRegistry.get(id)!;
  return {
    id: `app_${id}`,
    code,
    icon,
    name: m.name,
    status: m.health === "healthy" ? "healthy" : m.health,
    owner,
    permissions: m.permissions,
    version: m.version,
    health: m.health === "healthy" ? "ok" : m.health,
    lastUpdate: new Date().toISOString(),
    route: m.routes[0],
  };
}

const PLATFORM_APPS: RegisteredApplication[] = [
  {
    id: "app_port",
    code: "port_enterprise",
    icon: "PO",
    name: "Port Enterprise",
    status: "healthy",
    owner: "port",
    permissions: ["read", "navigate"],
    version: "4.6.0-enterprise",
    health: "ok",
    lastUpdate: new Date().toISOString(),
    route: "/workspace/port",
  },
  {
    id: "app_hub",
    code: "enterprise_hub",
    icon: "EH",
    name: "Enterprise Hub",
    status: "healthy",
    owner: "platform",
    permissions: ["read", "navigate"],
    version: "9.0.6",
    health: "ok",
    lastUpdate: new Date().toISOString(),
    route: "/workspace",
  },
  {
    id: "app_cc",
    code: "command_center",
    icon: "CC",
    name: "Command Center",
    status: "healthy",
    owner: "productivity",
    permissions: ["read", "navigate"],
    version: "9.0.6",
    health: "ok",
    lastUpdate: new Date().toISOString(),
    route: "/command-center",
  },
  {
    id: "app_cc_os",
    code: "command_center_os",
    icon: "CO",
    name: "Command Center OS",
    status: "healthy",
    owner: "platform_builder",
    permissions: ["read", "navigate"],
    version: "1.32.0",
    health: "ok",
    lastUpdate: new Date().toISOString(),
    route: "/platform-builder/command-center",
  },
  {
    id: "app_mc",
    code: "mission_control",
    icon: "MC",
    name: "Mission Control",
    status: "healthy",
    owner: "platform_builder",
    permissions: ["read", "navigate"],
    version: "1.32.0",
    health: "ok",
    lastUpdate: new Date().toISOString(),
    route: "/platform-builder/mission-control",
  },
  {
    id: "app_pilot",
    code: "pilot_dashboard",
    icon: "PI",
    name: "Pilot Dashboard",
    status: "healthy",
    owner: "platform",
    permissions: ["read", "navigate", "admin"],
    version: "1.32.0",
    health: "ok",
    lastUpdate: new Date().toISOString(),
    route: "/pilot",
  },
];

function buildApps(): RegisteredApplication[] {
  return [
    fromModule("auto", "auto_marketplace", "AU", "automotive"),
    fromModule("beauty", "beauty_enterprise", "BE", "beauty"),
    fromModule("cafe", "cafe_enterprise", "CA", "cafe"),
    fromModule("agro", "agro_enterprise", "AG", "agro"),
    fromModule("drone", "drone_enterprise", "DR", "drone"),
    fromModule("crypto", "crypto_enterprise", "CR", "crypto"),
    fromModule("legal", "legal_enterprise", "LE", "legal"),
    fromModule("finance", "finance_enterprise", "FI", "finance"),
    fromModule("marketplace", "marketplace", "MK", "marketplace"),
    fromModule("ai", "ai_os", "AI", "ai"),
    ...PLATFORM_APPS,
  ];
}

export const applicationRegistry = {
  list(): RegisteredApplication[] {
    return buildApps();
  },
  get(code: string): RegisteredApplication | undefined {
    return buildApps().find((a) => a.code === code || a.id === code);
  },
  count(): number {
    return buildApps().length;
  },
};
