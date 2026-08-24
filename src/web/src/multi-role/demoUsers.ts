/**
 * Sprint 42.1 — demo users for multi-role / multi-tenant parallel demos.
 * Password for all: demo
 */

import type { ViewModeId } from "@/ux-revolution/viewModeCatalog";
import type { RoleHomeId } from "@/navigation/roleHome";

export const MULTI_ROLE_DEMO_PASSWORD = "demo";

export type DemoUserDef = {
  email: string;
  name: string;
  company: string;
  tenantId: string;
  password: string;
  viewMode: ViewModeId;
  roleIds: string[];
  homeRole: RoleHomeId | "sales";
  /** Suggested vite port for parallel window */
  suggestedPort: number;
  workspaceSlot: string;
  businessType: string;
  modules: string[];
};

export const MULTI_ROLE_DEMO_USERS: DemoUserDef[] = [
  {
    email: "owner@ados.demo",
    name: "ADOS Owner",
    company: "ADOS Platform",
    tenantId: "ados",
    password: MULTI_ROLE_DEMO_PASSWORD,
    viewMode: "platform_owner",
    roleIds: ["owner", "platform_owner", "company_owner"],
    homeRole: "owner",
    suggestedPort: 3000,
    workspaceSlot: "owner",
    businessType: "platform",
    modules: ["owner", "analytics", "crm", "platform"],
  },
  {
    email: "admin@ados.demo",
    name: "ADOS Administrator",
    company: "ADOS Platform",
    tenantId: "ados",
    password: MULTI_ROLE_DEMO_PASSWORD,
    viewMode: "company_admin",
    roleIds: ["administrator", "admin"],
    homeRole: "administrator",
    suggestedPort: 3000,
    workspaceSlot: "owner",
    businessType: "platform",
    modules: ["admin", "crm", "analytics", "documents"],
  },
  {
    email: "travel@globefly.demo",
    name: "GlobeFly Travel",
    company: "GlobeFly Travel Agency",
    tenantId: "globefly",
    password: MULTI_ROLE_DEMO_PASSWORD,
    viewMode: "client",
    roleIds: ["client"],
    homeRole: "client",
    suggestedPort: 3001,
    workspaceSlot: "travel",
    businessType: "travel",
    modules: ["crm", "documents", "analytics", "tasks", "knowledge"],
  },
  {
    email: "crypto@ados.demo",
    name: "Crypto OTC Manager",
    company: "ADOS Crypto Desk",
    tenantId: "crypto-desk",
    password: MULTI_ROLE_DEMO_PASSWORD,
    viewMode: "manager",
    roleIds: ["manager", "sales"],
    homeRole: "manager",
    suggestedPort: 3002,
    workspaceSlot: "crypto",
    businessType: "crypto",
    modules: ["crypto", "crm", "analytics", "documents"],
  },
  {
    email: "build@ados.demo",
    name: "BuildCorp Client",
    company: "BuildCorp Construction",
    tenantId: "buildcorp",
    password: MULTI_ROLE_DEMO_PASSWORD,
    viewMode: "client",
    roleIds: ["client"],
    homeRole: "client",
    suggestedPort: 3003,
    workspaceSlot: "build",
    businessType: "construction",
    modules: ["crm", "documents", "tasks", "knowledge"],
  },
  {
    email: "drone@ados.demo",
    name: "DroneOps",
    company: "SkyFleet Drone Co",
    tenantId: "skyfleet",
    password: MULTI_ROLE_DEMO_PASSWORD,
    viewMode: "manager",
    roleIds: ["manager"],
    homeRole: "manager",
    suggestedPort: 3004,
    workspaceSlot: "drone",
    businessType: "drone",
    modules: ["drone", "crm", "documents", "analytics"],
  },
  {
    email: "auto@ados.demo",
    name: "Auto Dealer",
    company: "Prime Auto Dealer",
    tenantId: "prime-auto",
    password: MULTI_ROLE_DEMO_PASSWORD,
    viewMode: "manager",
    roleIds: ["manager", "dealer"],
    homeRole: "dealer",
    suggestedPort: 3005,
    workspaceSlot: "auto",
    businessType: "auto",
    modules: ["auto", "crm", "documents", "analytics"],
  },
  {
    email: "legal@ados.demo",
    name: "Law Office",
    company: "Lex & Partners",
    tenantId: "lex",
    password: MULTI_ROLE_DEMO_PASSWORD,
    viewMode: "client",
    roleIds: ["client"],
    homeRole: "client",
    suggestedPort: 3006,
    workspaceSlot: "legal",
    businessType: "legal",
    modules: ["legal", "documents", "knowledge", "tasks"],
  },
  {
    email: "agro@ados.demo",
    name: "Агрокомпания",
    company: "GreenField Agro",
    tenantId: "greenfield",
    password: MULTI_ROLE_DEMO_PASSWORD,
    viewMode: "manager",
    roleIds: ["manager"],
    homeRole: "manager",
    suggestedPort: 3007,
    workspaceSlot: "agro",
    businessType: "agro",
    modules: ["agro", "crm", "analytics", "documents"],
  },
  {
    email: "seller@ados.demo",
    name: "Marketplace Seller",
    company: "Market Seller Co",
    tenantId: "seller-co",
    password: MULTI_ROLE_DEMO_PASSWORD,
    viewMode: "client",
    roleIds: ["client"],
    homeRole: "client",
    suggestedPort: 3008,
    workspaceSlot: "seller",
    businessType: "marketplace",
    modules: ["marketplace", "crm", "documents", "analytics"],
  },
];

export function demoUserByEmail(email: string): DemoUserDef | undefined {
  const lower = email.trim().toLowerCase();
  return MULTI_ROLE_DEMO_USERS.find((u) => u.email === lower);
}

export function isMultiRoleDemoEmail(email: string): boolean {
  const lower = email.trim().toLowerCase();
  return (
    Boolean(demoUserByEmail(lower)) ||
    lower.endsWith("@ados.demo") ||
    lower.endsWith("@globefly.demo")
  );
}
