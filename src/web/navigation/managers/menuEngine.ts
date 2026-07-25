import type { MenuItem } from "../types";

const menu: MenuItem[] = [
  {
    id: "nav_workspace",
    name: "Workspace",
    icon: "workspace",
    route: "/workspace",
    module: "workspace",
    permissions: ["read"],
    status: "active",
    group: "core",
  },
  {
    id: "nav_identity",
    name: "Identity",
    icon: "security",
    route: "/identity",
    module: "identity",
    permissions: ["admin"],
    badge: "RBAC",
    status: "active",
    group: "core",
    children: [
      { id: "nav_users", name: "Users", icon: "crm", route: "/identity/users", module: "identity", permissions: ["admin"], status: "active" },
      { id: "nav_orgs", name: "Organizations", icon: "erp", route: "/identity/organizations", module: "identity", permissions: ["admin"], status: "active" },
    ],
  },
  {
    id: "nav_ai",
    name: "AI Platform",
    icon: "ai",
    route: "/workspace/dashboards/dash_ai",
    module: "ai",
    permissions: ["read"],
    status: "active",
    group: "intelligence",
    children: [
      { id: "nav_ai_agents", name: "Agents", icon: "ai", route: "/workspace/ai", module: "ai", permissions: ["read"], status: "active" },
    ],
  },
  {
    id: "nav_crm",
    name: "CRM",
    icon: "crm",
    route: "/workspace/crm",
    module: "crm",
    permissions: ["crm", "read"],
    status: "active",
    group: "business",
  },
  {
    id: "nav_erp",
    name: "ERP",
    icon: "erp",
    route: "/workspace/erp",
    module: "erp",
    permissions: ["erp", "read"],
    status: "active",
    group: "business",
  },
  {
    id: "nav_finance",
    name: "Finance",
    icon: "finance",
    route: "/workspace/finance",
    module: "finance",
    permissions: ["finance", "read"],
    status: "active",
    group: "business",
  },
  {
    id: "nav_analytics",
    name: "Analytics",
    icon: "analytics",
    route: "/workspace/analytics",
    module: "analytics",
    permissions: ["read"],
    status: "active",
    group: "intelligence",
  },
  {
    id: "nav_market",
    name: "Marketplace",
    icon: "workflow",
    route: "/workspace/marketplace",
    module: "marketplace",
    permissions: ["read"],
    badge: "new",
    status: "beta",
    group: "platform",
  },
  {
    id: "nav_navigation",
    name: "Navigation",
    icon: "navigation",
    route: "/navigation",
    module: "navigation",
    permissions: ["read"],
    status: "active",
    group: "platform",
  },
  {
    id: "nav_settings",
    name: "Settings",
    icon: "settings",
    route: "/settings",
    module: "settings",
    permissions: ["read"],
    status: "active",
    group: "core",
  },
];

function permitted(item: MenuItem, permissions: string[]): boolean {
  if (permissions.includes("admin")) return true;
  return item.permissions.some((p) => permissions.includes(p));
}

export const menuEngine = {
  all(): MenuItem[] {
    return structuredClone(menu);
  },
  forTenant(tenantId: string, permissions: string[]): MenuItem[] {
    const filterItem = (item: MenuItem): MenuItem | null => {
      if (item.tenantIds && !item.tenantIds.includes(tenantId)) return null;
      if (!permitted(item, permissions)) return null;
      const children = item.children?.map(filterItem).filter(Boolean) as MenuItem[] | undefined;
      return { ...item, children };
    };
    return menu.map(filterItem).filter(Boolean) as MenuItem[];
  },
  groups() {
    return [...new Set(menu.map((m) => m.group).filter(Boolean))] as string[];
  },
  nested(): MenuItem[] {
    return this.all().filter((m) => (m.children?.length || 0) > 0);
  },
  megaGroups() {
    return this.groups().map((g) => ({
      group: g,
      items: menu.filter((m) => m.group === g),
    }));
  },
};
