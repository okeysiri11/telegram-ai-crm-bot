/**
 * AI Runtime & Orchestration derivation — Sprint 33.2.
 * Pure client layer over live-ops aiOps + activity + workflows + integrations.
 * No new AI Core / Workflow Engine / Runtime Engine / Queue Engine.
 */

import type { LiveEnterpriseSnapshot } from "@/live-ops";
import type { AppNotification } from "@/notifications/notificationStore";
import { BUSINESS_WORKFLOW_TEMPLATES } from "@/enterprise-workflow/workflowTemplates";
import { deriveIntegrationHub } from "@/enterprise-integrations/deriveIntegrations";

export type RuntimeJobState = "active" | "waiting" | "completed" | "failed" | "paused";

export type RuntimePriority = "critical" | "high" | "normal" | "low";

export type RuntimeJob = {
  id: string;
  title: string;
  state: RuntimeJobState;
  executor: string;
  priority: RuntimePriority;
  source: string;
  waitSec: number;
  progress: number; // 0–100
  currentStep: string;
  nextStep: string;
  elapsedSec: number;
  aiCount: number;
  workflow?: string;
};

export type OrchestrationStep = {
  id: string;
  label: string;
  active: boolean;
  detail: string;
};

export type RuntimeHealth = {
  aiOnline: boolean;
  queueSize: number;
  activeExecutions: number;
  avgResponseMs: number;
  failedTasks: number;
  retries: number;
  needsIntervention: boolean;
};

export type RuntimeTwinView = {
  processesRunning: string[];
  aiInvolved: string[];
  integrationsUsed: string[];
};

export type RuntimeBundle = {
  counts: Record<RuntimeJobState, number>;
  jobs: RuntimeJob[];
  queue: RuntimeJob[];
  orchestration: OrchestrationStep[];
  monitor: {
    currentStep: string;
    nextStep: string;
    elapsedSec: number;
    aiCount: number;
    workflows: string[];
  };
  health: RuntimeHealth;
  twin: RuntimeTwinView;
};

const ORCH_CHAIN = [
  { id: "user", label: "User" },
  { id: "concierge", label: "Concierge" },
  { id: "ai_team", label: "AI Team" },
  { id: "workflow", label: "Workflow" },
  { id: "integrations", label: "Integrations" },
  { id: "knowledge", label: "Knowledge" },
  { id: "completed", label: "Completed" },
] as const;

const SOURCES = ["Mission Control", "Concierge", "Workflow", "CRM", "Integration Hub", "User"] as const;
const PRIORITIES: RuntimePriority[] = ["critical", "high", "normal", "low"];

function hash(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

function pickPriority(title: string): RuntimePriority {
  return PRIORITIES[hash(title) % PRIORITIES.length]!;
}

function pickSource(title: string, kind?: string): string {
  if (kind === "ai" || kind === "automation") return "Concierge";
  if (kind === "crm" || kind === "deal" || kind === "client") return "CRM";
  if (kind === "task") return "Workflow";
  return SOURCES[hash(title) % SOURCES.length]!;
}

export function deriveRuntime(
  snapshot: LiveEnterpriseSnapshot,
  notifications: AppNotification[] = [],
): RuntimeBundle {
  const ops = snapshot.aiOps;
  const intHub = deriveIntegrationHub(snapshot);
  const wfNames = BUSINESS_WORKFLOW_TEMPLATES.slice(0, 6).map((w) => w.title);

  const jobs: RuntimeJob[] = [];

  ops.running.forEach((title, i) => {
    const progress = 35 + (hash(title) % 50);
    jobs.push({
      id: `run_${i}_${hash(title)}`,
      title,
      state: "active",
      executor: title.includes("Concierge") ? "Concierge" : title,
      priority: pickPriority(title),
      source: "AI Team",
      waitSec: 0,
      progress,
      currentStep: progress < 50 ? "AI Team" : "Workflow",
      nextStep: progress < 70 ? "Integrations" : "Knowledge",
      elapsedSec: 20 + (hash(title) % 180),
      aiCount: 1 + (hash(title) % 3),
      workflow: wfNames[i % Math.max(wfNames.length, 1)],
    });
  });

  ops.queue.forEach((title, i) => {
    jobs.push({
      id: `wait_${i}_${hash(title)}`,
      title,
      state: "waiting",
      executor: "Queue · Concierge",
      priority: pickPriority(title),
      source: pickSource(title),
      waitSec: 15 + (hash(title) % 240),
      progress: 5 + (hash(title) % 20),
      currentStep: "Concierge",
      nextStep: "AI Team",
      elapsedSec: 0,
      aiCount: 0,
      workflow: wfNames[(i + 1) % Math.max(wfNames.length, 1)],
    });
  });

  ops.completed.forEach((title, i) => {
    jobs.push({
      id: `done_${i}_${hash(title)}`,
      title,
      state: "completed",
      executor: "AI Team",
      priority: "normal",
      source: pickSource(title),
      waitSec: 0,
      progress: 100,
      currentStep: "Completed",
      nextStep: "—",
      elapsedSec: 60 + (hash(title) % 300),
      aiCount: 1 + (hash(title) % 2),
      workflow: wfNames[i % Math.max(wfNames.length, 1)],
    });
  });

  ops.errors.forEach((title, i) => {
    jobs.push({
      id: `fail_${i}_${hash(title)}`,
      title,
      state: "failed",
      executor: "Runtime",
      priority: "critical",
      source: "Mission Control",
      waitSec: 0,
      progress: 40 + (hash(title) % 30),
      currentStep: "Integrations",
      nextStep: "Retry",
      elapsedSec: 30 + (hash(title) % 90),
      aiCount: 1,
      workflow: wfNames[0],
    });
  });

  // Paused from unread workflow notifications
  notifications
    .filter((n) => n.kind === "workflow" && !n.read)
    .slice(0, 2)
    .forEach((n, i) => {
      jobs.push({
        id: `pause_${n.id}`,
        title: n.title,
        state: "paused",
        executor: "Awaiting user",
        priority: "high",
        source: "Notification Center",
        waitSec: 60 + i * 30,
        progress: 55,
        currentStep: "User",
        nextStep: "Concierge",
        elapsedSec: 90,
        aiCount: 1,
        workflow: wfNames[i % Math.max(wfNames.length, 1)],
      });
    });

  // If still empty paused set, seed one idle pause from recent
  if (!jobs.some((j) => j.state === "paused") && ops.recent[0]) {
    jobs.push({
      id: `pause_seed`,
      title: `Paused · ${ops.recent[0]}`,
      state: "paused",
      executor: "Awaiting approval",
      priority: "normal",
      source: "Workflow",
      waitSec: 45,
      progress: 48,
      currentStep: "Workflow",
      nextStep: "Integrations",
      elapsedSec: 120,
      aiCount: 1,
      workflow: wfNames[0],
    });
  }

  const counts: Record<RuntimeJobState, number> = {
    active: jobs.filter((j) => j.state === "active").length,
    waiting: jobs.filter((j) => j.state === "waiting").length,
    completed: jobs.filter((j) => j.state === "completed").length,
    failed: jobs.filter((j) => j.state === "failed").length,
    paused: jobs.filter((j) => j.state === "paused").length,
  };

  const queue = jobs
    .filter((j) => j.state === "waiting" || j.state === "active" || j.state === "paused")
    .sort((a, b) => {
      const order = { critical: 0, high: 1, normal: 2, low: 3 };
      return order[a.priority] - order[b.priority] || b.waitSec - a.waitSec;
    });

  const focus = jobs.find((j) => j.state === "active") || jobs.find((j) => j.state === "waiting") || jobs[0];

  const activeIdx =
    focus?.state === "completed"
      ? ORCH_CHAIN.length - 1
      : focus?.currentStep === "Concierge"
        ? 1
        : focus?.currentStep === "AI Team"
          ? 2
          : focus?.currentStep === "Workflow"
            ? 3
            : focus?.currentStep === "Integrations"
              ? 4
              : focus?.currentStep === "Knowledge"
                ? 5
                : focus?.currentStep === "User"
                  ? 0
                  : 2;

  const orchestration: OrchestrationStep[] = ORCH_CHAIN.map((s, i) => ({
    id: s.id,
    label: s.label,
    active: i === activeIdx,
    detail:
      i === activeIdx
        ? focus?.title || "in flight"
        : i < activeIdx
          ? "done"
          : "pending",
  }));

  const avgResponseMs =
    80 +
    ops.queue.length * 40 +
    ops.errors.length * 120 +
    (ops.running.length ? 60 : 20);

  const health: RuntimeHealth = {
    aiOnline: ops.running.length > 0 || ops.status === "ok" || ops.status === "operational" || ops.status === "seed",
    queueSize: ops.queue.length + counts.waiting,
    activeExecutions: counts.active,
    avgResponseMs,
    failedTasks: counts.failed,
    retries: counts.failed + Math.min(2, counts.paused),
    needsIntervention: counts.failed > 0 || counts.paused > 0,
  };

  const twin: RuntimeTwinView = {
    processesRunning: jobs.filter((j) => j.state === "active").map((j) => j.workflow || j.title).slice(0, 6),
    aiInvolved: [...new Set(ops.running.concat(jobs.filter((j) => j.state === "active").map((j) => j.executor)))].slice(0, 6),
    integrationsUsed: intHub.twin.connectedSystems.slice(0, 6),
  };

  return {
    counts,
    jobs,
    queue,
    orchestration,
    monitor: {
      currentStep: focus?.currentStep || "Idle",
      nextStep: focus?.nextStep || "—",
      elapsedSec: focus?.elapsedSec || 0,
      aiCount: focus?.aiCount || ops.running.length,
      workflows: [...new Set(jobs.map((j) => j.workflow).filter(Boolean) as string[])].slice(0, 5),
    },
    health,
    twin,
  };
}

export { ORCH_CHAIN };
