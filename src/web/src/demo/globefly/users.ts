/** Sprint 41.1 — GlobeFly demo users (password: demo). */

import { GLOBEFLY_TENANT_ID } from "./tenant";
import type { ViewModeId } from "@/ux-revolution";

export type GlobeFlyDemoUser = {
  email: string;
  name: string;
  roleLabel: string;
  defaultViewMode: ViewModeId;
  roleIds: string[];
};

export const GLOBEFLY_DEMO_USERS: GlobeFlyDemoUser[] = [
  {
    email: "owner@globefly.demo",
    name: "GlobeFly Owner",
    roleLabel: "Company Owner",
    defaultViewMode: "platform_owner",
    roleIds: ["owner", "company_owner"],
  },
  {
    email: "admin@globefly.demo",
    name: "GlobeFly Admin",
    roleLabel: "Company Administrator",
    defaultViewMode: "company_admin",
    roleIds: ["administrator"],
  },
  {
    email: "manager@globefly.demo",
    name: "GlobeFly Manager",
    roleLabel: "Manager",
    defaultViewMode: "manager",
    roleIds: ["manager"],
  },
  {
    email: "sales@globefly.demo",
    name: "GlobeFly Sales",
    roleLabel: "Sales Manager",
    defaultViewMode: "manager",
    roleIds: ["manager"],
  },
  {
    email: "operator@globefly.demo",
    name: "GlobeFly Operator",
    roleLabel: "Operator",
    defaultViewMode: "manager",
    roleIds: ["employee"],
  },
  {
    email: "client@globefly.demo",
    name: "GlobeFly Client",
    roleLabel: "Client",
    defaultViewMode: "client",
    roleIds: ["client"],
  },
];

export function isGlobeFlyEmail(email: string): boolean {
  return email.toLowerCase().endsWith("@globefly.demo");
}

export function globeFlyUserByEmail(email: string): GlobeFlyDemoUser | undefined {
  return GLOBEFLY_DEMO_USERS.find((u) => u.email.toLowerCase() === email.toLowerCase());
}

export function resolveGlobeFlyTenant(email: string, tenantId: string): string {
  if (isGlobeFlyEmail(email)) return GLOBEFLY_TENANT_ID;
  return tenantId || GLOBEFLY_TENANT_ID;
}
