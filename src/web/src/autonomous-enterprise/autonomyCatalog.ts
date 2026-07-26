/**
 * Autonomous Enterprise catalog — Sprint 33.5.
 * Autonomy levels + approval categories over existing RBAC / Workspace.
 * No new AI Core / Automation Engine / Runtime Engine.
 */

export type AutonomyLevel = 0 | 1 | 2 | 3 | 4;

export type ApprovalCategory =
  | "crm"
  | "finance"
  | "legal"
  | "documents"
  | "ai_team"
  | "workflow";

export type RiskLevel = "low" | "medium" | "high" | "critical";

export type ApprovalStatus = "pending" | "approved" | "rejected" | "edited";

export type AutonomyLevelDef = {
  level: AutonomyLevel;
  title: string;
  summary: string;
  allowsAuto: boolean;
  requiresApprovalForCritical: boolean;
};

export const AUTONOMY_LEVELS: AutonomyLevelDef[] = [
  {
    level: 0,
    title: "Manual Only",
    summary: "Только ручные действия пользователя",
    allowsAuto: false,
    requiresApprovalForCritical: true,
  },
  {
    level: 1,
    title: "AI Suggests",
    summary: "AI предлагает, человек исполняет",
    allowsAuto: false,
    requiresApprovalForCritical: true,
  },
  {
    level: 2,
    title: "AI Executes Low Risk",
    summary: "AI выполняет низкорисковые действия",
    allowsAuto: true,
    requiresApprovalForCritical: true,
  },
  {
    level: 3,
    title: "AI Executes + Approval For Critical",
    summary: "Автономность + HITL для критичных решений",
    allowsAuto: true,
    requiresApprovalForCritical: true,
  },
  {
    level: 4,
    title: "Enterprise Autonomous",
    summary: "Максимальная автономность в рамках политики",
    allowsAuto: true,
    requiresApprovalForCritical: true,
  },
];

export const APPROVAL_CATEGORIES: Array<{ id: ApprovalCategory; label: string }> = [
  { id: "crm", label: "CRM" },
  { id: "finance", label: "Finance" },
  { id: "legal", label: "Legal" },
  { id: "documents", label: "Documents" },
  { id: "ai_team", label: "AI Team" },
  { id: "workflow", label: "Workflow" },
];

/** Actions that always need confirmation at levels ≤3 (and policy at L4). */
export const CRITICAL_ACTIONS = [
  "Finance payment > threshold",
  "Legal contract send",
  "CRM mass update",
  "Disable integration",
  "Change autonomy level",
  "Delete documents",
  "AI Team policy change",
] as const;

export function levelLabel(level: AutonomyLevel): string {
  return AUTONOMY_LEVELS.find((l) => l.level === level)?.title || `Level ${level}`;
}

export function resolveDefaultLevel(roleId?: string): AutonomyLevel {
  const r = (roleId || "").toLowerCase();
  if (r.includes("owner") || r.includes("executive") || r.includes("admin")) return 3;
  if (r.includes("manager")) return 2;
  if (r.includes("operator") || r.includes("agent")) return 1;
  return 1;
}
