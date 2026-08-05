/**
 * Sprint 27.1 — Enterprise Dashboard module cards.
 * Large openable tiles for core business surfaces (clean Sprint 27.2 URLs).
 */

import type { ShellIconId } from "@/shell/enterprise/enterpriseNav";

export type EnterpriseModuleCard = {
  id: string;
  label: string;
  description: string;
  route: string;
  icon: ShellIconId;
  stats: { label: string; value: string }[];
};

export const ENTERPRISE_MODULE_CARDS: EnterpriseModuleCard[] = [
  {
    id: "crm",
    label: "CRM",
    description: "Clients, pipeline, and deal velocity",
    route: "/crm",
    icon: "crm",
    stats: [
      { label: "Clients", value: "4 812" },
      { label: "Deals", value: "186" },
    ],
  },
  {
    id: "erp",
    label: "ERP",
    description: "Operations, inventory, and fulfillment",
    route: "/erp",
    icon: "erp",
    stats: [
      { label: "Orders", value: "312" },
      { label: "SLA", value: "98%" },
    ],
  },
  {
    id: "projects",
    label: "Projects",
    description: "Workspace delivery and milestones",
    route: "/projects",
    icon: "projects",
    stats: [
      { label: "Active", value: "24" },
      { label: "At risk", value: "3" },
    ],
  },
  {
    id: "ai_agents",
    label: "AI Agents",
    description: "Team of specialists running live work",
    route: "/ai-agents",
    icon: "ai_agents",
    stats: [
      { label: "Running", value: "7" },
      { label: "Done today", value: "42" },
    ],
  },
  {
    id: "knowledge",
    label: "Knowledge",
    description: "Enterprise memory and playbooks",
    route: "/knowledge",
    icon: "knowledge",
    stats: [
      { label: "Articles", value: "1.2k" },
      { label: "Fresh", value: "91%" },
    ],
  },
  {
    id: "analytics",
    label: "Analytics",
    description: "KPIs, trends, and executive views",
    route: "/analytics",
    icon: "analytics",
    stats: [
      { label: "Dashboards", value: "18" },
      { label: "Alerts", value: "5" },
    ],
  },
  {
    id: "finance",
    label: "Finance",
    description: "Treasury, payments, and CFO pulse",
    route: "/workspace/finance",
    icon: "erp",
    stats: [
      { label: "Cash", value: "₴ 8.4M" },
      { label: "AP/AR", value: "stable" },
    ],
  },
  {
    id: "marketplace",
    label: "Marketplace",
    description: "Solutions, templates, and installables",
    route: "/marketplace",
    icon: "marketplace",
    stats: [
      { label: "Solutions", value: "64" },
      { label: "Installed", value: "11" },
    ],
  },
  {
    id: "automation",
    label: "Automation",
    description: "Workflows, triggers, and agents at work",
    route: "/automation",
    icon: "automation",
    stats: [
      { label: "Flows", value: "57" },
      { label: "Success", value: "96%" },
    ],
  },
  {
    id: "security",
    label: "Security",
    description: "Identity, sessions, and governance",
    route: "/security",
    icon: "security",
    stats: [
      { label: "Sessions", value: "ok" },
      { label: "Risk", value: "low" },
    ],
  },
];
