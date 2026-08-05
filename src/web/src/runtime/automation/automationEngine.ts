/**
 * Enterprise Automation Engine — Sprint 28.9.
 * Orchestrates triggers · queue · policies on top of Workflow Runtime.
 */

import { commandRuntime } from "@/runtime/commandRuntime";
import { workflowRuntime } from "@/runtime/workflowRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { automationRegistry } from "./automationRegistry";
import { automationQueue } from "./automationQueue";
import { automationHistory } from "./automationHistory";
import { automationTriggers } from "./automationTriggers";
import { automationScheduler } from "./automationScheduler";
import { computeBackoffDelay, validateAutomation } from "./automationPolicies";
import {
  AUTOMATION_ENGINE_VERSION,
  type AutomationDefinition,
  type AutomationJob,
  type AutomationTriggerKind,
} from "./automationTypes";

let booted = false;
let pumping = false;
const pausedAutomations = new Set<string>();

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

function seedAutomations() {
  automationRegistry.register({
    id: "auto_pulse_parallel",
    name: "Ops Parallel Pulse",
    description: "Manual / Command trigger → demo_parallel_ops workflow",
    workflowId: "demo_parallel_ops",
    enabled: true,
    tags: ["ops", "demo"],
    triggers: [
      { kind: "manual" },
      { kind: "command", commandId: "auto_run" },
      { kind: "ai_intent", intentMatch: "pulse" },
    ],
    policy: { retryCount: 1, timeoutMs: 30_000, backoffMs: 300, concurrency: 2, priority: 70, errorPolicy: "retry" },
  });

  automationRegistry.register({
    id: "auto_new_client",
    name: "New Client Flow",
    description: "CRM / AI intent → tpl_new_client",
    workflowId: "tpl_new_client",
    enabled: true,
    tags: ["crm"],
    triggers: [
      { kind: "manual" },
      { kind: "ai_intent", intentMatch: "client" },
      { kind: "event_bus", eventType: "open_module" },
    ],
    policy: { retryCount: 2, timeoutMs: 45_000, backoffMs: 400, concurrency: 1, priority: 60, errorPolicy: "retry" },
  });

  automationRegistry.register({
    id: "auto_on_startup",
    name: "Startup Health Automation",
    description: "Runs parallel pulse once on shell startup (enable to activate)",
    workflowId: "demo_parallel_ops",
    enabled: false,
    tags: ["startup"],
    triggers: [{ kind: "startup" }],
    policy: { retryCount: 0, timeoutMs: 20_000, backoffMs: 0, concurrency: 1, priority: 40, errorPolicy: "fail" },
  });

  automationRegistry.register({
    id: "auto_after_workflow",
    name: "Chain After Workflow Completed",
    description: "When any workflow completes → wait_event demo (manual-gated via event)",
    workflowId: "demo_wait_event",
    enabled: false,
    tags: ["chain"],
    triggers: [{ kind: "workflow_completed" }],
    policy: { retryCount: 0, timeoutMs: 15_000, backoffMs: 0, concurrency: 1, priority: 30, errorPolicy: "skip" },
  });

  automationRegistry.register({
    id: "auto_scheduled_pulse",
    name: "Scheduled Pulse (disabled)",
    description: "Schedule trigger example — disabled by default",
    workflowId: "demo_parallel_ops",
    enabled: false,
    tags: ["schedule"],
    triggers: [{ kind: "schedule", scheduleMs: 120_000 }],
    policy: { retryCount: 1, timeoutMs: 20_000, backoffMs: 500, concurrency: 1, priority: 20, errorPolicy: "retry" },
  });
}

function registerCommands() {
  commandRuntime.register({
    id: "auto_open_center",
    action: "open_automation_center",
    label: "Open Automation Center",
    kind: "navigate",
    keywords: ["automation", "center", "queue"],
    route: "/automation",
    permission: "*",
  });
  commandRuntime.register({
    id: "auto_run",
    action: "run_automation",
    label: "Run Automation",
    kind: "run_workflow",
    keywords: ["automation", "run"],
    permission: "*",
    handler: async (_ctx, args) => {
      const id = String(args.automationId || args.id || "auto_pulse_parallel");
      const res = await automationEngine.runAutomation(id, "command", args);
      return { ok: res.ok, message: res.jobId, error: res.error };
    },
  });
}

async function executeJob(job: AutomationJob) {
  const automation = automationRegistry.get(job.automationId);
  if (!automation) {
    automationQueue.update(job.id, { status: "failed", error: "automation_missing", finishedAt: new Date().toISOString() }, {
      type: "failed",
      message: "automation_missing",
    });
    return;
  }

  if (pausedAutomations.has(automation.id)) {
    automationQueue.update(job.id, { status: "waiting" }, { type: "waiting", message: "automation_paused" });
    return;
  }

  automationQueue.update(
    job.id,
    { status: "running", startedAt: new Date().toISOString() },
    { type: "running", message: `Starting workflow ${automation.workflowId}` },
  );

  enterpriseEventBus.publish({
    type: "workflow_update",
    source: "system",
    payload: { stream: "automation", jobId: job.id, automationId: automation.id, status: "running" },
  });

  const timeoutMs = automation.policy.timeoutMs;
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
  }, timeoutMs);

  try {
    const result = await workflowRuntime.start(automation.workflowId, {
      via: "automation",
      automationId: automation.id,
      jobId: job.id,
      triggerKind: job.triggerKind,
    });
    clearTimeout(timer);

    if (timedOut) {
      if (result.sessionId) workflowRuntime.cancel(result.sessionId);
      await failOrRetry(job, automation, "timeout");
      return;
    }

    if (!result.ok) {
      await failOrRetry(job, automation, result.error || "workflow_start_failed");
      return;
    }

    const session = result.session || workflowRuntime.getSession(result.sessionId!);
    const status = session?.status;
    if (status === "failed") {
      await failOrRetry(job, automation, "workflow_failed");
      return;
    }
    if (status === "waiting" || status === "paused") {
      automationQueue.update(
        job.id,
        { status: "waiting", workflowSessionId: result.sessionId },
        { type: "waiting", message: `Workflow ${status}` },
      );
      return;
    }

    const finishedAt = new Date().toISOString();
    const started = job.startedAt || finishedAt;
    const durationMs = Math.max(0, Date.now() - new Date(started).getTime());
    automationQueue.update(
      job.id,
      {
        status: "completed",
        workflowSessionId: result.sessionId,
        finishedAt,
        durationMs,
      },
      { type: "completed", message: "Automation completed" },
    );
    automationHistory.push({
      jobId: job.id,
      automationId: automation.id,
      workflowId: automation.workflowId,
      status: "completed",
      triggerKind: job.triggerKind,
      attempt: job.attempt,
      durationMs,
    });
  } catch (e) {
    clearTimeout(timer);
    await failOrRetry(job, automation, e instanceof Error ? e.message : "automation_error");
  }
}

async function failOrRetry(job: AutomationJob, automation: AutomationDefinition, error: string) {
  const policy = automation.policy;
  const canRetry =
    policy.errorPolicy === "retry" && job.attempt <= policy.retryCount;

  if (canRetry) {
    const delay = computeBackoffDelay(policy, job.attempt);
    const nextRetryAt = new Date(Date.now() + delay).toISOString();
    automationQueue.update(
      job.id,
      {
        status: "retry",
        error,
        attempt: job.attempt + 1,
        nextRetryAt,
      },
      { type: "retry", message: `Retry in ${delay}ms (${error})` },
    );
    setTimeout(() => {
      const live = automationQueue.get(job.id);
      if (!live || live.status === "cancelled") return;
      automationQueue.update(job.id, { status: "pending", nextRetryAt: undefined }, {
        type: "requeued",
        message: "Retry queued",
      });
      void pumpQueue();
    }, delay);
    return;
  }

  if (policy.errorPolicy === "skip" || policy.errorPolicy === "continue") {
    automationQueue.update(
      job.id,
      {
        status: "completed",
        error,
        finishedAt: new Date().toISOString(),
      },
      { type: "skipped", message: `Skipped failure: ${error}` },
    );
    automationHistory.push({
      jobId: job.id,
      automationId: automation.id,
      workflowId: automation.workflowId,
      status: "completed",
      triggerKind: job.triggerKind,
      attempt: job.attempt,
      error,
    });
    return;
  }

  const finishedAt = new Date().toISOString();
  const started = job.startedAt || finishedAt;
  const durationMs = Math.max(0, Date.now() - new Date(started).getTime());
  automationQueue.update(
    job.id,
    { status: "failed", error, finishedAt, durationMs },
    { type: "failed", message: error },
  );
  automationHistory.push({
    jobId: job.id,
    automationId: automation.id,
    workflowId: automation.workflowId,
    status: "failed",
    triggerKind: job.triggerKind,
    attempt: job.attempt,
    durationMs,
    error,
  });
}

async function pumpQueue() {
  if (pumping) return;
  pumping = true;
  try {
    // Determine concurrency from highest-priority pending jobs' automations
    const pending = automationQueue.list("pending");
    const running = automationQueue.list("running").length;
    // Use max concurrency among enabled automations (default 2)
    let maxConc = 2;
    for (const a of automationRegistry.list()) {
      if (a.enabled) maxConc = Math.max(maxConc, a.policy.concurrency);
    }
    const slots = Math.max(0, maxConc - running);
    const batch = pending.slice(0, slots);
    await Promise.all(batch.map((j) => executeJob(j)));
  } finally {
    pumping = false;
    if (automationQueue.list("pending").length && automationQueue.list("running").length === 0) {
      void pumpQueue();
    }
  }
}

function enqueue(
  automationId: string,
  triggerKind: AutomationTriggerKind,
  extra?: Record<string, unknown>,
) {
  const automation = automationRegistry.get(automationId);
  if (!automation || !automation.enabled) return null;
  if (pausedAutomations.has(automationId) && triggerKind !== "manual") return null;

  // Respect per-automation concurrency
  const activeForAuto = automationQueue
    .list()
    .filter(
      (j) =>
        j.automationId === automationId &&
        (j.status === "running" || j.status === "pending" || j.status === "retry" || j.status === "waiting"),
    ).length;
  if (activeForAuto >= automation.policy.concurrency && triggerKind !== "manual") {
    return null;
  }

  const job = automationQueue.enqueue({
    id: uid("aj"),
    automationId,
    workflowId: automation.workflowId,
    status: "pending",
    priority: automation.policy.priority,
    attempt: 1,
    triggerKind,
    createdAt: new Date().toISOString(),
  });
  void extra;
  void pumpQueue();
  return job;
}

export const automationEngine = {
  version: AUTOMATION_ENGINE_VERSION,

  startup() {
    if (booted) {
      return this.stats();
    }
    workflowRuntime.startup();
    commandRuntime.startup();
    seedAutomations();
    automationTriggers.bind((id, kind, extra) => {
      enqueue(id, kind, extra);
    });
    automationTriggers.attach();
    automationTriggers.syncSchedules();
    registerCommands();
    booted = true;
    automationTriggers.fireStartup();
    enterpriseEventBus.publish({
      type: "runtime_update",
      source: "system",
      payload: { stream: "automation", ready: true, version: AUTOMATION_ENGINE_VERSION },
    });
    return this.stats();
  },

  shutdown() {
    automationTriggers.fireShutdown();
    automationTriggers.detach();
    automationScheduler.clear();
    booted = false;
  },

  isReady() {
    return booted;
  },

  registerAutomation(
    input: Parameters<typeof automationRegistry.register>[0],
  ) {
    this.startup();
    const res = automationRegistry.register(input);
    if (res.ok) automationTriggers.syncSchedules();
    return res;
  },

  validateAutomation(def: AutomationDefinition) {
    return validateAutomation(def);
  },

  async runAutomation(
    automationId: string,
    triggerKind: AutomationTriggerKind = "manual",
    _extra?: Record<string, unknown>,
  ) {
    this.startup();
    const job = enqueue(automationId, triggerKind, _extra);
    if (!job) return { ok: false, error: "enqueue_failed" };
    // Wait briefly for pump to start
    await pumpQueue();
    return { ok: true, jobId: job.id, job: automationQueue.get(job.id) };
  },

  cancelAutomation(jobId: string) {
    const job = automationQueue.get(jobId);
    if (!job) return { ok: false, error: "job_not_found" };
    if (job.workflowSessionId) workflowRuntime.cancel(job.workflowSessionId);
    automationQueue.update(
      jobId,
      { status: "cancelled", finishedAt: new Date().toISOString() },
      { type: "cancelled", message: "Cancelled" },
    );
    automationHistory.push({
      jobId,
      automationId: job.automationId,
      workflowId: job.workflowId,
      status: "cancelled",
      triggerKind: job.triggerKind,
      attempt: job.attempt,
    });
    return { ok: true };
  },

  pauseAutomation(automationId: string) {
    pausedAutomations.add(automationId);
    for (const j of automationQueue.list("running")) {
      if (j.automationId === automationId) {
        automationQueue.update(j.id, { status: "waiting" }, { type: "paused", message: "Paused" });
        if (j.workflowSessionId) workflowRuntime.pause(j.workflowSessionId);
      }
    }
    return { ok: true };
  },

  resumeAutomation(automationId: string) {
    pausedAutomations.delete(automationId);
    for (const j of automationQueue.list("waiting")) {
      if (j.automationId === automationId) {
        automationQueue.update(j.id, { status: "pending" }, { type: "resumed", message: "Resumed" });
        if (j.workflowSessionId) void workflowRuntime.resume(j.workflowSessionId);
      }
    }
    void pumpQueue();
    return { ok: true };
  },

  async retryAutomation(jobId: string) {
    const job = automationQueue.get(jobId);
    if (!job) return { ok: false, error: "job_not_found" };
    automationQueue.update(
      jobId,
      { status: "pending", attempt: job.attempt + 1, error: undefined },
      { type: "manual_retry", message: "Manual retry" },
    );
    await pumpQueue();
    return { ok: true, job: automationQueue.get(jobId) };
  },

  listAutomations() {
    this.startup();
    return automationRegistry.list();
  },

  listQueue(status?: Parameters<typeof automationQueue.list>[0]) {
    return automationQueue.list(status);
  },

  history(limit = 40) {
    return automationHistory.list(limit);
  },

  fireWebhook(token: string, payload?: Record<string, unknown>) {
    this.startup();
    automationTriggers.fireWebhook(token, payload);
  },

  stats() {
    const hist = automationHistory.stats();
    const counts = automationQueue.counts();
    return {
      version: AUTOMATION_ENGINE_VERSION,
      automations: automationRegistry.list().length,
      enabled: automationRegistry.list().filter((a) => a.enabled).length,
      queue: counts,
      history: hist,
      schedules: automationScheduler.list().length,
      paused: pausedAutomations.size,
    };
  },

  inspectorSnapshot() {
    this.startup();
    return {
      version: AUTOMATION_ENGINE_VERSION,
      automations: automationRegistry.list(),
      queue: automationQueue.list(),
      history: automationHistory.list(40),
      stats: this.stats(),
      schedules: automationScheduler.list(),
      timeline: automationQueue
        .list()
        .flatMap((j) => j.timeline.map((t) => ({ ...t, jobId: j.id, automationId: j.automationId })))
        .sort((a, b) => b.at.localeCompare(a.at))
        .slice(0, 60),
    };
  },

  /** Vitest / isolated reset — not for production callers */
  __resetForTests() {
    automationTriggers.detach();
    automationScheduler.clear();
    automationRegistry.clear();
    automationQueue.clear();
    automationHistory.clear();
    pausedAutomations.clear();
    booted = false;
    pumping = false;
  },
};
