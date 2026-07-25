export type CatalogEntry = {
  id: string;
  name: string;
  api: string;
  properties: string[];
  examples: string[];
  usageRules: string[];
  accessibilityNotes: string[];
};

export const componentCatalog: CatalogEntry[] = [
  {
    id: "buttons",
    name: "Buttons",
    api: "Button",
    properties: ["variant", "size", "disabled"],
    examples: ["primary", "secondary", "danger"],
    usageRules: ["Use primary for main actions", "One primary per view"],
    accessibilityNotes: ["Must be focusable", "Disabled state announced"],
  },
  {
    id: "forms",
    name: "Forms",
    api: "Input | Select | Checkbox | Switch | Radio | DatePicker",
    properties: ["value", "onChange", "label", "error"],
    examples: ["login form", "settings form"],
    usageRules: ["Associate labels", "Show validation inline"],
    accessibilityNotes: ["Use aria-invalid", "Describe errors"],
  },
  {
    id: "cards",
    name: "Cards",
    api: "Card",
    properties: ["title", "children"],
    examples: ["dashboard widget"],
    usageRules: ["Prefer for interactive groupings"],
    accessibilityNotes: ["Heading hierarchy"],
  },
  {
    id: "tables",
    name: "Tables",
    api: "Table | DataGrid | Pagination",
    properties: ["headers", "rows", "page"],
    examples: ["tenant list"],
    usageRules: ["Keep headers sticky when long"],
    accessibilityNotes: ["Use th/scope"],
  },
  {
    id: "charts",
    name: "Charts",
    api: "Charts",
    properties: ["labels", "values"],
    examples: ["KPI line"],
    usageRules: ["Provide text summary"],
    accessibilityNotes: ["Do not rely on color alone"],
  },
  {
    id: "navigation",
    name: "Navigation",
    api: "Sidebar | TopNavigation | Breadcrumbs",
    properties: ["active", "favorites"],
    examples: ["module nav"],
    usageRules: ["Keep landmarks"],
    accessibilityNotes: ["nav landmarks", "aria-current"],
  },
  {
    id: "dialogs",
    name: "Dialogs",
    api: "Dialog | Modal | Drawer",
    properties: ["open", "onClose", "title"],
    examples: ["confirm"],
    usageRules: ["Trap focus while open"],
    accessibilityNotes: ["role=dialog", "Escape closes"],
  },
  {
    id: "modals",
    name: "Modals",
    api: "Modal",
    properties: ["open", "title", "onClose"],
    examples: ["detail modal"],
    usageRules: ["Avoid nested modals"],
    accessibilityNotes: ["Focus return on close"],
  },
  {
    id: "notifications",
    name: "Notifications",
    api: "NotificationsPanel",
    properties: ["kind", "read"],
    examples: ["toast", "in-app"],
    usageRules: ["Do not spam critical alerts"],
    accessibilityNotes: ["aria-live polite/assertive"],
  },
  {
    id: "dashboards",
    name: "Dashboards",
    api: "DashboardPage widgets",
    properties: ["layout", "widgets"],
    examples: ["home dashboard"],
    usageRules: ["Use dashboard grid"],
    accessibilityNotes: ["Readable order"],
  },
  {
    id: "ai_widgets",
    name: "AI Widgets",
    api: "AI assistant card",
    properties: ["prompt", "status"],
    examples: ["assistant panel"],
    usageRules: ["Owner approval for actions"],
    accessibilityNotes: ["Announce status changes"],
  },
  {
    id: "data_grids",
    name: "Data Grids",
    api: "DataGrid",
    properties: ["columns", "rows"],
    examples: ["records grid"],
    usageRules: ["Paginate large sets"],
    accessibilityNotes: ["Keyboard sortable headers when added"],
  },
];
