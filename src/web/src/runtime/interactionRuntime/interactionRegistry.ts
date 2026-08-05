/**
 * Interaction registry — object kinds + context action catalog (runtime-driven).
 */

import type { ContextActionDef, InteractionActionId, InteractionObjectKind } from "./interactionTypes";

const ACTIONS: ContextActionDef[] = [
  {
    id: "open_building",
    label: "Open Building",
    targetKinds: ["building"],
    permission: "public",
    keywords: ["building", "open", "city"],
  },
  {
    id: "open_company",
    label: "Open Company",
    targetKinds: ["company", "building"],
    permission: "public",
    keywords: ["company", "business", "ebn"],
  },
  {
    id: "open_citizen",
    label: "Open Citizen",
    targetKinds: ["citizen"],
    permission: "citizen",
    keywords: ["citizen", "person", "profile"],
  },
  {
    id: "open_asset",
    label: "Open Asset",
    targetKinds: ["asset", "vehicle"],
    permission: "company",
    keywords: ["asset", "inventory"],
  },
  {
    id: "open_district",
    label: "Open District",
    targetKinds: ["district"],
    permission: "public",
    keywords: ["district", "area"],
  },
  {
    id: "open_project",
    label: "Open Project",
    targetKinds: ["project"],
    permission: "citizen",
    keywords: ["project"],
  },
  {
    id: "open_meeting",
    label: "Open Meeting",
    targetKinds: ["meeting"],
    permission: "citizen",
    keywords: ["meeting"],
  },
  {
    id: "open_vehicle",
    label: "Open Vehicle",
    targetKinds: ["vehicle"],
    permission: "company",
    keywords: ["vehicle", "fleet"],
  },
  {
    id: "start_workflow",
    label: "Start Workflow",
    targetKinds: ["building", "company", "project", "citizen"],
    permission: "company",
    keywords: ["workflow", "start"],
  },
  {
    id: "assign_task",
    label: "Assign Task",
    targetKinds: ["citizen", "project"],
    permission: "manager",
    keywords: ["task", "assign"],
  },
  {
    id: "invite_partner",
    label: "Invite Partner",
    targetKinds: ["company"],
    permission: "company",
    keywords: ["partner", "invite", "ebn"],
  },
  {
    id: "launch_ai",
    label: "Launch AI",
    targetKinds: ["ai_agent", "citizen", "building"],
    permission: "citizen",
    keywords: ["ai", "agent", "launch"],
  },
  {
    id: "create_meeting",
    label: "Create Meeting",
    targetKinds: ["building", "citizen", "company", "meeting"],
    permission: "citizen",
    keywords: ["meeting", "create"],
  },
  {
    id: "navigate",
    label: "Navigate",
    targetKinds: ["building", "district", "company", "citizen", "asset"],
    permission: "public",
    keywords: ["navigate", "go", "jump"],
  },
];

const KIND_ROUTES: Partial<Record<InteractionObjectKind, string>> = {
  building: "/enterprise-city",
  company: "/business-network",
  citizen: "/digital-citizens",
  asset: "/assets",
  vehicle: "/assets",
  district: "/spatial",
  project: "/life-engine",
  meeting: "/life-engine",
  ai_agent: "/digital-citizens",
};

export const interactionRegistry = {
  actions() {
    return [...ACTIONS];
  },

  getAction(id: InteractionActionId) {
    return ACTIONS.find((a) => a.id === id);
  },

  actionsForKind(kind: InteractionObjectKind) {
    return ACTIONS.filter((a) => a.targetKinds.includes(kind));
  },

  defaultRoute(kind: InteractionObjectKind) {
    return KIND_ROUTES[kind] || "/city-visualization";
  },

  kinds(): InteractionObjectKind[] {
    return [
      "building",
      "company",
      "citizen",
      "asset",
      "project",
      "vehicle",
      "ai_agent",
      "district",
      "meeting",
    ];
  },
};
