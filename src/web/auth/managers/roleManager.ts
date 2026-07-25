import type { Role } from "../types";

const roles: Role[] = [
  { roleId: "role_sys_admin", name: "System Admin", scope: "system", inheritsFrom: [], permissionGroups: ["administration", "api_access"], template: "system_admin" },
  { roleId: "role_org_owner", name: "Organization Owner", scope: "organization", inheritsFrom: ["role_sys_admin"], permissionGroups: ["crm", "erp", "finance", "hr"], template: "org_owner" },
  { roleId: "role_proj_lead", name: "Project Lead", scope: "project", inheritsFrom: ["role_org_owner"], permissionGroups: ["analytics", "ai_agents"], template: "project_lead" },
  { roleId: "role_custom_analyst", name: "Custom Analyst", scope: "custom", inheritsFrom: [], permissionGroups: ["analytics", "marketplace"], template: "analyst" },
];

export const roleManager = {
  list(): Role[] {
    return [...roles];
  },
  systemRoles() {
    return roles.filter((r) => r.scope === "system");
  },
  organizationRoles() {
    return roles.filter((r) => r.scope === "organization");
  },
  projectRoles() {
    return roles.filter((r) => r.scope === "project");
  },
  customRoles() {
    return roles.filter((r) => r.scope === "custom");
  },
  templates() {
    return [...new Set(roles.map((r) => r.template).filter(Boolean))];
  },
};
