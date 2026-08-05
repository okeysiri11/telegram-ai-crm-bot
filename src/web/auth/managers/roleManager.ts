import type { Role } from "../types";

/** Sprint 30.1 enterprise role catalog */
const roles: Role[] = [
  { roleId: "role_owner", name: "Owner", scope: "organization", inheritsFrom: [], permissionGroups: ["administration", "api_access", "finance", "crm", "erp"], template: "owner" },
  { roleId: "role_administrator", name: "Administrator", scope: "organization", inheritsFrom: ["role_owner"], permissionGroups: ["administration", "api_access", "crm", "erp"], template: "administrator" },
  { roleId: "role_manager", name: "Manager", scope: "organization", inheritsFrom: [], permissionGroups: ["crm", "analytics", "ai_agents"], template: "manager" },
  { roleId: "role_employee", name: "Employee", scope: "organization", inheritsFrom: [], permissionGroups: ["crm"], template: "employee" },
  { roleId: "role_client", name: "Client", scope: "organization", inheritsFrom: [], permissionGroups: ["marketplace"], template: "client" },
  { roleId: "role_dealer", name: "Dealer", scope: "organization", inheritsFrom: [], permissionGroups: ["crm", "marketplace"], template: "dealer" },
  { roleId: "role_partner", name: "Partner", scope: "organization", inheritsFrom: [], permissionGroups: ["marketplace", "analytics"], template: "partner" },
  { roleId: "role_accountant", name: "Accountant", scope: "organization", inheritsFrom: [], permissionGroups: ["finance"], template: "accountant" },
  { roleId: "role_lawyer", name: "Lawyer", scope: "organization", inheritsFrom: [], permissionGroups: ["administration"], template: "lawyer" },
  { roleId: "role_production", name: "Production", scope: "organization", inheritsFrom: [], permissionGroups: ["erp", "analytics"], template: "production" },
  { roleId: "role_viewer", name: "Viewer", scope: "organization", inheritsFrom: [], permissionGroups: ["analytics"], template: "viewer" },
  // legacy retained
  { roleId: "role_platform_owner", name: "Platform Owner", scope: "system", inheritsFrom: [], permissionGroups: ["administration", "api_access", "platform_owner", "builder"], template: "platform_owner" },
  { roleId: "role_sys_admin", name: "System Admin", scope: "system", inheritsFrom: [], permissionGroups: ["administration", "api_access"], template: "system_admin" },
];

export const roleManager = {
  list(): Role[] {
    return [...roles];
  },
  enterpriseRoles() {
    return roles.filter((r) =>
      [
        "Owner",
        "Administrator",
        "Manager",
        "Employee",
        "Client",
        "Dealer",
        "Partner",
        "Accountant",
        "Lawyer",
        "Production",
        "Viewer",
      ].includes(r.name),
    );
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
  resolve(roleName: string): Role | undefined {
    const n = roleName.toLowerCase();
    return roles.find((r) => r.name.toLowerCase() === n || r.roleId === roleName || r.template === n);
  },
};
