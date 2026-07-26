/**
 * Business workflow templates — Sprint 32.7.
 * Mirrors Enterprise Hub TEMPLATE_KINDS + display aliases.
 * No new Workflow / Automation Engine.
 */

import type { CityBuildingId } from "@/enterprise-city";

export type WorkflowStepKind =
  | "start"
  | "ai"
  | "module"
  | "knowledge"
  | "notification"
  | "finish";

export type WorkflowTemplateStep = {
  id: string;
  label: string;
  kind: WorkflowStepKind;
  agent?: string;
};

export type BusinessWorkflowTemplate = {
  id: string;
  hubKind: string;
  title: string;
  description: string;
  /** Human-facing library label (SECTION 5). */
  libraryLabel: string;
  steps: WorkflowTemplateStep[];
  aiChain: string[];
  cityPath: CityBuildingId[];
};

export const BUSINESS_WORKFLOW_TEMPLATES: BusinessWorkflowTemplate[] = [
  {
    id: "new_client",
    hubKind: "crm_lead_processing",
    title: "Новый клиент",
    libraryLabel: "Новый клиент",
    description: "Lead → Marketing → Sales → Knowledge → Notification",
    steps: [
      { id: "s1", label: "Client Created", kind: "start" },
      { id: "s2", label: "Marketing AI", kind: "ai", agent: "Marketing" },
      { id: "s3", label: "Sales AI", kind: "ai", agent: "Sales" },
      { id: "s4", label: "Analytics AI", kind: "ai", agent: "Analytics" },
      { id: "s5", label: "Knowledge", kind: "knowledge" },
      { id: "s6", label: "Notification", kind: "notification" },
      { id: "s7", label: "Completed", kind: "finish" },
    ],
    aiChain: ["Concierge", "Marketing", "Sales", "Analytics", "Completed"],
    cityPath: ["crm", "marketing", "sales", "knowledge", "concierge"],
  },
  {
    id: "sale",
    hubKind: "crm_lead_processing",
    title: "Продажа",
    libraryLabel: "Продажа",
    description: "Сделка через Sales → Finance → Analytics",
    steps: [
      { id: "s1", label: "Deal Opened", kind: "start" },
      { id: "s2", label: "Sales AI", kind: "ai", agent: "Sales" },
      { id: "s3", label: "Finance AI", kind: "ai", agent: "Finance" },
      { id: "s4", label: "Analytics AI", kind: "ai", agent: "Analytics" },
      { id: "s5", label: "Notification", kind: "notification" },
      { id: "s6", label: "Completed", kind: "finish" },
    ],
    aiChain: ["Concierge", "Sales", "Finance", "Analytics", "Completed"],
    cityPath: ["crm", "sales", "finance", "analytics"],
  },
  {
    id: "contract",
    hubKind: "contract_approval",
    title: "Подписание договора",
    libraryLabel: "Подписание договора",
    description: "Documents → Legal check → Finance → Knowledge",
    steps: [
      { id: "s1", label: "Contract Draft", kind: "start" },
      { id: "s2", label: "Legal AI", kind: "ai", agent: "Legal" },
      { id: "s3", label: "Finance AI", kind: "ai", agent: "Finance" },
      { id: "s4", label: "Knowledge", kind: "knowledge" },
      { id: "s5", label: "Notification", kind: "notification" },
      { id: "s6", label: "Completed", kind: "finish" },
    ],
    aiChain: ["Concierge", "Legal", "Finance", "Completed"],
    cityPath: ["documents", "finance", "knowledge", "admin"],
  },
  {
    id: "project",
    hubKind: "ai_task_processing",
    title: "Создание проекта",
    libraryLabel: "Создание проекта",
    description: "AI Team оркестрирует запуск проекта",
    steps: [
      { id: "s1", label: "Project Request", kind: "start" },
      { id: "s2", label: "Concierge", kind: "ai", agent: "Concierge" },
      { id: "s3", label: "Ops AI", kind: "ai", agent: "Operations" },
      { id: "s4", label: "Knowledge", kind: "knowledge" },
      { id: "s5", label: "Completed", kind: "finish" },
    ],
    aiChain: ["Concierge", "Operations", "Analytics", "Completed"],
    cityPath: ["ai_team", "mission_control", "dashboard", "knowledge"],
  },
  {
    id: "request",
    hubKind: "customer_support",
    title: "Новая заявка",
    libraryLabel: "Новая заявка",
    description: "Support intake → CRM → Knowledge",
    steps: [
      { id: "s1", label: "Ticket Created", kind: "start" },
      { id: "s2", label: "Concierge", kind: "ai", agent: "Concierge" },
      { id: "s3", label: "Sales AI", kind: "ai", agent: "Sales" },
      { id: "s4", label: "Knowledge", kind: "knowledge" },
      { id: "s5", label: "Notification", kind: "notification" },
      { id: "s6", label: "Completed", kind: "finish" },
    ],
    aiChain: ["Concierge", "Sales", "Completed"],
    cityPath: ["crm", "knowledge", "concierge", "hub"],
  },
  {
    id: "invoice",
    hubKind: "invoice_approval",
    title: "Согласование счёта",
    libraryLabel: "Согласование счёта",
    description: "Finance approval chain (Hub invoice_approval)",
    steps: [
      { id: "s1", label: "Invoice Received", kind: "start" },
      { id: "s2", label: "Finance AI", kind: "ai", agent: "Finance" },
      { id: "s3", label: "Legal AI", kind: "ai", agent: "Legal" },
      { id: "s4", label: "Notification", kind: "notification" },
      { id: "s5", label: "Completed", kind: "finish" },
    ],
    aiChain: ["Concierge", "Finance", "Legal", "Completed"],
    cityPath: ["finance", "documents", "admin", "mission_control"],
  },
  {
    id: "onboarding",
    hubKind: "employee_onboarding",
    title: "Онбординг сотрудника",
    libraryLabel: "Онбординг сотрудника",
    description: "HR → Admin → Knowledge (Hub employee_onboarding)",
    steps: [
      { id: "s1", label: "Hire Started", kind: "start" },
      { id: "s2", label: "Ops AI", kind: "ai", agent: "Operations" },
      { id: "s3", label: "Knowledge", kind: "knowledge" },
      { id: "s4", label: "Notification", kind: "notification" },
      { id: "s5", label: "Completed", kind: "finish" },
    ],
    aiChain: ["Concierge", "Operations", "Completed"],
    cityPath: ["hr", "admin", "knowledge"],
  },
  {
    id: "maintenance",
    hubKind: "equipment_maintenance",
    title: "Обслуживание оборудования",
    libraryLabel: "Обслуживание оборудования",
    description: "Production → Mission Control (Hub equipment_maintenance)",
    steps: [
      { id: "s1", label: "Maintenance Due", kind: "start" },
      { id: "s2", label: "Ops AI", kind: "ai", agent: "Operations" },
      { id: "s3", label: "Notification", kind: "notification" },
      { id: "s4", label: "Completed", kind: "finish" },
    ],
    aiChain: ["Concierge", "Operations", "Completed"],
    cityPath: ["production", "mission_control", "hr"],
  },
];

export function getWorkflowTemplate(id: string): BusinessWorkflowTemplate | undefined {
  return BUSINESS_WORKFLOW_TEMPLATES.find((t) => t.id === id || t.hubKind === id);
}
