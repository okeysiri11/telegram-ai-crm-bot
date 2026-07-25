export const navigationHub = {
  features: [
    "sidebar",
    "top_navigation",
    "breadcrumbs",
    "favorites",
    "recent_pages",
    "module_switcher",
    "global_search",
  ] as const,
  modules: [
    { id: "hub", label: "Hub", path: "/" },
    { id: "workspace", label: "Workspace", path: "/workspace" },
    { id: "identity", label: "Identity", path: "/identity" },
    { id: "ai", label: "AI", path: "/workspace/ai" },
    { id: "crm", label: "CRM", path: "/workspace/crm" },
    { id: "erp", label: "ERP", path: "/workspace/erp" },
    { id: "analytics", label: "Analytics", path: "/workspace/analytics" },
    { id: "marketplace", label: "Marketplace", path: "/workspace/marketplace" },
  ],
};
