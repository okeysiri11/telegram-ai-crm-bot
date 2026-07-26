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
    id: "nav_platform_builder",
    name: "Platform Builder",
    icon: "workflow",
    route: "/platform-builder",
    module: "platform_builder",
    permissions: ["read", "builder"],
    badge: "new",
    status: "active",
    group: "platform",
    children: [
      { id: "nav_pb_dash", name: "Dashboard", icon: "analytics", route: "/platform-builder", module: "platform_builder", permissions: ["read"], status: "active" },
      { id: "nav_pb_framework", name: "Universal Framework", icon: "workflow", route: "/platform-builder/framework", module: "platform_builder", permissions: ["read"], status: "active" },
      { id: "nav_pb_vertical", name: "Vertical Builder", icon: "erp", route: "/platform-builder/vertical", module: "platform_builder", permissions: ["read"], status: "active" },
      { id: "nav_pb_ai", name: "AI Builder", icon: "ai", route: "/platform-builder/ai", module: "platform_builder", permissions: ["read"], status: "beta" },
      { id: "nav_pb_concierge", name: "Concierge Builder", icon: "ai", route: "/platform-builder/concierge", module: "platform_builder", permissions: ["read"], status: "beta" },
      { id: "nav_pb_ai_team", name: "AI Team Center", icon: "ai", route: "/platform-builder/ai-team", module: "platform_builder", permissions: ["read"], status: "beta" },
      { id: "nav_pb_collab", name: "Collaborative AI", icon: "ai", route: "/platform-builder/collaborative-ai", module: "platform_builder", permissions: ["read"], status: "active" },
      { id: "nav_pb_ops", name: "AI Operations Center", icon: "analytics", route: "/platform-builder/operations", module: "platform_builder", permissions: ["read"], status: "active" },
      { id: "nav_pb_team_map", name: "AI Team Map", icon: "ai", route: "/platform-builder/team-map", module: "platform_builder", permissions: ["read"], status: "active" },
      { id: "nav_pb_visual_behavior", name: "Visual Behavior", icon: "analytics", route: "/platform-builder/visual-behavior", module: "platform_builder", permissions: ["read"], status: "active" },
      { id: "nav_pb_rendering", name: "Visual Rendering", icon: "analytics", route: "/platform-builder/rendering", module: "platform_builder", permissions: ["read"], status: "active" },
      { id: "nav_pb_themes", name: "Visual Themes", icon: "analytics", route: "/platform-builder/themes", module: "platform_builder", permissions: ["read"], status: "active" },
      { id: "nav_pb_assets", name: "Visual Assets", icon: "analytics", route: "/platform-builder/assets", module: "platform_builder", permissions: ["read"], status: "active" },
      { id: "nav_pb_simulation", name: "Visual Simulation", icon: "analytics", route: "/platform-builder/simulation", module: "platform_builder", permissions: ["read"], status: "active" },
      { id: "nav_pb_director", name: "Visual Director", icon: "analytics", route: "/platform-builder/director", module: "platform_builder", permissions: ["read"], status: "active" },
      { id: "nav_pb_story", name: "Visual Stories", icon: "analytics", route: "/platform-builder/story", module: "platform_builder", permissions: ["read"], status: "active" },
      { id: "nav_pb_intelligence", name: "Visual Intelligence", icon: "analytics", route: "/platform-builder/intelligence", module: "platform_builder", permissions: ["read"], status: "active" },
      { id: "nav_pb_experience", name: "Visual Experience", icon: "analytics", route: "/platform-builder/experience", module: "platform_builder", permissions: ["read"], status: "active" },
      { id: "nav_pb_workspace_os", name: "Workspace OS", icon: "analytics", route: "/platform-builder/workspace-os", module: "platform_builder", permissions: ["read"], status: "active" },
      { id: "nav_pb_crm", name: "CRM Builder", icon: "crm", route: "/platform-builder/crm", module: "platform_builder", permissions: ["read"], status: "beta" },
      { id: "nav_pb_erp", name: "ERP Builder", icon: "erp", route: "/platform-builder/erp", module: "platform_builder", permissions: ["read"], status: "beta" },
      { id: "nav_pb_workflow", name: "Workflow Builder", icon: "workflow", route: "/platform-builder/workflow", module: "platform_builder", permissions: ["read"], status: "beta" },
      { id: "nav_pb_knowledge", name: "Knowledge Builder", icon: "analytics", route: "/platform-builder/knowledge", module: "platform_builder", permissions: ["read"], status: "beta" },
      { id: "nav_pb_automation", name: "Automation Builder", icon: "workflow", route: "/platform-builder/automation", module: "platform_builder", permissions: ["read"], status: "beta" },
      { id: "nav_pb_dash_builder", name: "Dashboard Builder", icon: "analytics", route: "/platform-builder/dashboard-builder", module: "platform_builder", permissions: ["read"], status: "beta" },
      { id: "nav_pb_template", name: "Template Builder", icon: "workflow", route: "/platform-builder/template", module: "platform_builder", permissions: ["read"], status: "beta" },
      { id: "nav_pb_marketplace", name: "Marketplace Builder", icon: "workflow", route: "/platform-builder/marketplace", module: "platform_builder", permissions: ["read"], status: "beta" },
      { id: "nav_pb_academy", name: "Builder Academy 2.0", icon: "analytics", route: "/platform-builder/academy", module: "platform_builder", permissions: ["read"], status: "active" },
      { id: "nav_pb_god", name: "God Mode", icon: "security", route: "/platform-builder/god-mode", module: "platform_builder", permissions: ["platform_owner"], status: "active" },
    ],
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
  if (permissions.includes("admin") || permissions.includes("platform_owner")) return true;
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
