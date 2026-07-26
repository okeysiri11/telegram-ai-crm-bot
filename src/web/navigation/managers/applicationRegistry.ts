import type { RegisteredApplication } from "../types";

const APPS: RegisteredApplication[] = [
  { id: "app_auto", code: "auto_marketplace", icon: "AU", name: "Auto Marketplace", status: "healthy", owner: "automotive", permissions: ["read", "navigate"], version: "4.2.0-enterprise", health: "ok", lastUpdate: new Date().toISOString(), route: "/workspace/auto" },
  { id: "app_beauty", code: "beauty_enterprise", icon: "BE", name: "Beauty Enterprise", status: "healthy", owner: "beauty", permissions: ["read", "navigate"], version: "1.0.0-shell", health: "ok", lastUpdate: new Date().toISOString(), route: "/workspace/beauty" },
  { id: "app_cafe", code: "cafe_enterprise", icon: "CA", name: "Cafe Enterprise", status: "healthy", owner: "cafe", permissions: ["read", "navigate"], version: "1.0.0-shell", health: "ok", lastUpdate: new Date().toISOString(), route: "/workspace/cafe" },
  { id: "app_agro", code: "agro_enterprise", icon: "AG", name: "Agro Enterprise", status: "healthy", owner: "agro", permissions: ["read", "navigate"], version: "4.4.0-enterprise", health: "ok", lastUpdate: new Date().toISOString(), route: "/workspace/agro" },
  { id: "app_drone", code: "drone_enterprise", icon: "DR", name: "Drone Enterprise", status: "healthy", owner: "drone", permissions: ["read", "navigate"], version: "1.0.0-shell", health: "ok", lastUpdate: new Date().toISOString(), route: "/workspace/drone" },
  { id: "app_port", code: "port_enterprise", icon: "PO", name: "Port Enterprise", status: "healthy", owner: "port", permissions: ["read", "navigate"], version: "4.6.0-enterprise", health: "ok", lastUpdate: new Date().toISOString(), route: "/workspace/port" },
  { id: "app_crypto", code: "crypto_enterprise", icon: "CR", name: "Crypto Enterprise (Bidex)", status: "healthy", owner: "crypto", permissions: ["read", "navigate"], version: "4.8.0-enterprise", health: "ok", lastUpdate: new Date().toISOString(), route: "/workspace/crypto" },
  { id: "app_legal", code: "legal_enterprise", icon: "LE", name: "Legal Enterprise", status: "healthy", owner: "legal", permissions: ["read", "navigate"], version: "5.0.0-enterprise", health: "ok", lastUpdate: new Date().toISOString(), route: "/workspace/legal" },
  { id: "app_fin", code: "finance_enterprise", icon: "FI", name: "Finance Enterprise", status: "healthy", owner: "finance", permissions: ["read", "navigate"], version: "5.2.0-enterprise", health: "ok", lastUpdate: new Date().toISOString(), route: "/workspace/finance" },
  { id: "app_hub", code: "enterprise_hub", icon: "EH", name: "Enterprise Hub", status: "healthy", owner: "platform", permissions: ["read", "navigate"], version: "9.0.6", health: "ok", lastUpdate: new Date().toISOString(), route: "/workspace" },
  { id: "app_mkt", code: "marketplace", icon: "MK", name: "AI Marketplace", status: "healthy", owner: "marketplace", permissions: ["read", "navigate"], version: "1.0", health: "ok", lastUpdate: new Date().toISOString(), route: "/workspace/marketplace" },
  { id: "app_cc", code: "command_center", icon: "CC", name: "Command Center", status: "healthy", owner: "productivity", permissions: ["read", "navigate"], version: "9.0.6", health: "ok", lastUpdate: new Date().toISOString(), route: "/command-center" },
  { id: "app_cc_os", code: "command_center_os", icon: "CO", name: "Command Center OS", status: "healthy", owner: "platform_builder", permissions: ["read", "navigate"], version: "1.29.0", health: "ok", lastUpdate: new Date().toISOString(), route: "/platform-builder/command-center" },
  { id: "app_mc", code: "mission_control", icon: "MC", name: "Mission Control", status: "healthy", owner: "platform_builder", permissions: ["read", "navigate"], version: "1.29.0", health: "ok", lastUpdate: new Date().toISOString(), route: "/platform-builder/mission-control" },
  { id: "app_aios", code: "ai_os", icon: "AI", name: "AI OS", status: "healthy", owner: "ai", permissions: ["read", "navigate"], version: "3.4.0-alpha", health: "ok", lastUpdate: new Date().toISOString(), route: "/workspace/ai" },
];

export const applicationRegistry = {
  list(): RegisteredApplication[] {
    return [...APPS];
  },
  get(code: string): RegisteredApplication | undefined {
    return APPS.find((a) => a.code === code || a.id === code);
  },
  count(): number {
    return APPS.length;
  },
};
