/**
 * Enterprise Workflow Automation derivation — Sprint 32.7.
 * Pure client layer over LiveEnterpriseSnapshot + templates.
 * No new Workflow / Automation Engine / Store.
 */

import type { LiveEnterpriseSnapshot } from "@/live-ops";
import type { AppNotification } from "@/notifications/notificationStore";
import type { CityBuildingId } from "@/enterprise-city";
import {
  BUSINESS_WORKFLOW_TEMPLATES,
  getWorkflowTemplate,
  type BusinessWorkflowTemplate,
  type WorkflowTemplateStep,
} from "./workflowTemplates";

export type WorkflowRunStatus = "active" | "completed" | "waiting" | "error";

export type WorkflowRun = {
  id: string;
  templateId: string;
  title: string;
  status: WorkflowRunStatus;
  durationMin: number;
  currentExecutor: string;
  nextStep: string;
  result: string;
  stepIndex: number;
  steps: WorkflowTemplateStep[];
  aiChain: string[];
  cityPath: CityBuildingId[];
  hubKind: string;
};

export type WorkflowExecutiveMetrics = {
  completedToday: number;
  automated: number;
  timeSavedMin: number;
  activeCount: number;
  errorCount: number;
};

export type WorkflowAutomationBundle = {
  active: WorkflowRun[];
  completed: WorkflowRun[];
  waiting: WorkflowRun[];
  errors: WorkflowRun[];
  monitor: WorkflowRun | null;
  templates: BusinessWorkflowTemplate[];
  metrics: WorkflowExecutiveMetrics;
  /** Primary city route for active automation */
  cityRoute: CityBuildingId[];
  cityTemplateId: string | null;
};

function hash(seed: string): number {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) % 97;
  return h;
}

function pickTemplates(snapshot: LiveEnterpriseSnapshot): BusinessWorkflowTemplate[] {
  const blob = [
    ...snapshot.aiOps.running,
    ...snapshot.aiOps.queue,
    ...snapshot.aiOps.completed,
    ...snapshot.aiOps.recent,
    ...snapshot.activity.map((a) => `${a.title} ${a.detail} ${a.moduleHint || ""}`),
  ]
    .join(" ")
    .toLowerCase();

  const scored = BUSINESS_WORKFLOW_TEMPLATES.map((t) => {
    let score = 1;
    if (/crm|lead|client|клиент|сделк/.test(blob) && (t.id === "new_client" || t.id === "sale")) score += 3;
    if (/invoice|financ|счёт|счет/.test(blob) && t.id === "invoice") score += 3;
    if (/contract|договор|legal|document/.test(blob) && t.id === "contract") score += 3;
    if (/project|задач|ai task/.test(blob) && t.id === "project") score += 2;
    if (/support|заявк|ticket/.test(blob) && t.id === "request") score += 2;
    if (/maintain|production|оборуд/.test(blob) && t.id === "maintenance") score += 2;
    if (/onboard|hr|сотрудник/.test(blob) && t.id === "onboarding") score += 2;
    if (snapshot.activeModules.some((m) => t.cityPath.includes(m as CityBuildingId))) score += 1;
    return { t, score };
  }).sort((a, b) => b.score - a.score);

  return scored.map((s) => s.t);
}

function makeRun(
  template: BusinessWorkflowTemplate,
  status: WorkflowRunStatus,
  seed: string,
  snapshot: LiveEnterpriseSnapshot,
): WorkflowRun {
  const steps = template.steps;
  let stepIndex = 0;
  if (status === "completed") stepIndex = steps.length - 1;
  else if (status === "waiting") stepIndex = Math.max(1, Math.min(steps.length - 2, 2));
  else if (status === "error") stepIndex = Math.max(1, Math.min(steps.length - 2, 3));
  else stepIndex = 1 + (hash(seed) % Math.max(1, steps.length - 2));

  const current = steps[stepIndex] || steps[0];
  const next = steps[stepIndex + 1];
  const durationMin =
    status === "completed"
      ? 8 + (hash(seed) % 20)
      : status === "waiting"
        ? 2 + (hash(seed) % 6)
        : 3 + (hash(seed + snapshot.aiOps.status) % 12);

  const result =
    status === "completed"
      ? snapshot.aiOps.completed[0] || "Workflow завершён"
      : status === "error"
        ? snapshot.aiOps.errors[0] || "Требуется вмешательство"
        : status === "waiting"
          ? "Ожидает следующий шаг / approval"
          : current.label;

  return {
    id: `wf_${template.id}_${status}_${hash(seed)}`,
    templateId: template.id,
    title: template.title,
    status,
    durationMin,
    currentExecutor: current.agent || current.label,
    nextStep: next?.label || "—",
    result,
    stepIndex,
    steps,
    aiChain: template.aiChain,
    cityPath: template.cityPath,
    hubKind: template.hubKind,
  };
}

export function deriveWorkflowAutomation(
  snapshot: LiveEnterpriseSnapshot,
  notifications: AppNotification[] = [],
  preferredTemplateId?: string | null,
): WorkflowAutomationBundle {
  const ranked = pickTemplates(snapshot);
  const preferred =
    (preferredTemplateId && getWorkflowTemplate(preferredTemplateId)) || ranked[0] || BUSINESS_WORKFLOW_TEMPLATES[0];

  const activeCount = Math.max(1, Math.min(3, snapshot.aiOps.running.length || 1));
  const waitingCount = Math.min(2, snapshot.aiOps.queue.length || (notifications.filter((n) => !n.read).length ? 1 : 0));
  const errorCount = Math.min(2, snapshot.aiOps.errors.length);
  const completedCount = Math.max(1, Math.min(4, snapshot.aiOps.completed.length || snapshot.aiOps.recent.length || 1));

  const active: WorkflowRun[] = [];
  for (let i = 0; i < activeCount; i++) {
    const tpl = i === 0 ? preferred : ranked[i % ranked.length];
    active.push(makeRun(tpl, "active", `a${i}${tpl.id}`, snapshot));
  }

  const waiting: WorkflowRun[] = [];
  for (let i = 0; i < waitingCount; i++) {
    const tpl = ranked[(i + 1) % ranked.length];
    waiting.push(makeRun(tpl, "waiting", `w${i}${tpl.id}`, snapshot));
  }

  const errors: WorkflowRun[] = [];
  for (let i = 0; i < errorCount; i++) {
    const tpl = ranked[(i + 2) % ranked.length];
    errors.push(makeRun(tpl, "error", `e${i}${tpl.id}`, snapshot));
  }

  const completed: WorkflowRun[] = [];
  for (let i = 0; i < completedCount; i++) {
    const tpl = ranked[(i + 3) % ranked.length];
    completed.push(makeRun(tpl, "completed", `c${i}${tpl.id}`, snapshot));
  }

  const monitor = active[0] || waiting[0] || errors[0] || completed[0] || null;
  const automated = active.length + completed.length;
  const timeSavedMin = completed.reduce((s, r) => s + r.durationMin, 0) + active.length * 5;

  return {
    active,
    completed,
    waiting,
    errors,
    monitor,
    templates: BUSINESS_WORKFLOW_TEMPLATES,
    metrics: {
      completedToday: completed.length,
      automated,
      timeSavedMin,
      activeCount: active.length,
      errorCount: errors.length,
    },
    cityRoute: monitor?.cityPath || preferred.cityPath,
    cityTemplateId: monitor?.templateId || preferred.id,
  };
}
