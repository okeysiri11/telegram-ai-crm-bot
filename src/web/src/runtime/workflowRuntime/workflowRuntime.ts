/**
 * Enterprise Workflow Runtime — Sprint 28.8.
 * One execution engine over Command Runtime + Event Bus. No parallel runtimes.
 */

import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { workflowRegistry } from "./workflowRegistry";
import { workflowHistory } from "./workflowHistory";
import { createWorkflowSession, logSession, workflowSessions, hydrateSessions } from "./workflowSession";
import { advanceSession, attachWorkflowEventBridge } from "./workflowExecution";
import { buildSeedWorkflows } from "./workflowCatalog";
import {
  WORKFLOW_RUNTIME_VERSION,
  type WorkflowDefinition,
  type WorkflowSession,
  type WorkflowStartResult,
} from "./workflowTypes";

let booted = false;
let busUnsub: (() => void) | null = null;

function recordTerminal(session: WorkflowSession) {
  const def = workflowRegistry.get(session.definitionId);
  const ended =
    session.status === "completed" ||
    session.status === "failed" ||
    session.status === "cancelled";
  if (!ended) return;
  workflowHistory.push({
    sessionId: session.id,
    definitionId: session.definitionId,
    name: def?.name || session.definitionId,
    status: session.status,
    startedAt: session.startedAt,
    completedAt: session.completedAt || session.updatedAt,
    durationMs: Math.max(
      0,
      new Date(session.completedAt || session.updatedAt).getTime() - new Date(session.startedAt).getTime(),
    ),
    error: Object.values(session.nodeRecords).find((r) => r.error)?.error,
  });
}

function registerCommands() {
  commandRuntime.register({
    id: "wf_open_inspector",
    action: "open_workflow_inspector",
    label: "Open Workflow Runtime Inspector",
    kind: "navigate",
    keywords: ["workflow", "runtime", "inspector"],
    route: "/workflow-runtime",
    permission: "*",
    minRole: "developer",
  });
  commandRuntime.register({
    id: "wf_start",
    action: "start_workflow",
    label: "Start Workflow",
    kind: "run_workflow",
    keywords: ["workflow", "start", "run"],
    permission: "*",
    handler: async (_ctx, args) => {
      const id = String(args.workflowId || args.id || "demo_parallel_ops");
      const res = await workflowRuntime.start(id, args);
      return { ok: res.ok, message: res.sessionId, error: res.error, data: res as unknown as Record<string, unknown> };
    },
  });
}

export const workflowRuntime = {
  version: WORKFLOW_RUNTIME_VERSION,

  startup() {
    if (!booted) {
      workflowRegistry.registerMany(buildSeedWorkflows());
      hydrateSessions();
      busUnsub?.();
      busUnsub = attachWorkflowEventBridge();
      commandRuntime.startup();
      registerCommands();
      booted = true;
      enterpriseEventBus.publish({
        type: "workflow_update",
        source: "system",
        payload: { stream: "workflow_runtime", ready: true, version: WORKFLOW_RUNTIME_VERSION },
      });
    }
    return {
      version: WORKFLOW_RUNTIME_VERSION,
      definitions: workflowRegistry.list().length,
      sessions: workflowSessions.list().length,
    };
  },

  isReady() {
    return booted;
  },

  register(def: WorkflowDefinition) {
    this.startup();
    return workflowRegistry.register(def);
  },

  listDefinitions() {
    this.startup();
    return workflowRegistry.list();
  },

  getDefinition(id: string) {
    this.startup();
    return workflowRegistry.get(id);
  },

  listSessions() {
    return workflowSessions.list();
  },

  getSession(id: string) {
    return workflowSessions.get(id);
  },

  history(limit = 40) {
    return workflowHistory.list(limit);
  },

  async start(
    definitionId: string,
    vars: Record<string, unknown> = {},
  ): Promise<WorkflowStartResult> {
    this.startup();
    const def = workflowRegistry.get(definitionId);
    if (!def) return { ok: false, error: "workflow_not_found" };
    const session = createWorkflowSession(def, vars);
    workflowSessions.set(session);
    enterpriseEventBus.publish({
      type: "workflow_update",
      source: "system",
      payload: { sessionId: session.id, status: "running", definitionId },
    });
    const live = await advanceSession(session.id);
    if (live) recordTerminal(live);
    return { ok: true, sessionId: session.id, session: live || session };
  },

  /**
   * AI → Command Runtime → Workflow Runtime only.
   */
  async startFromAi(utterance: string, definitionId?: string) {
    this.startup();
    const result = await commandRuntime.routeAiIntent(utterance);
    const aiIntent =
      result && typeof result === "object" && "intent" in result
        ? (result as { intent?: { intent?: string } }).intent?.intent
        : undefined;
    const id =
      definitionId ||
      (String(aiIntent || utterance).toLowerCase().includes("crm") ||
      utterance.toLowerCase().includes("client")
        ? "tpl_new_client"
        : "demo_parallel_ops");
    // Must go through command path when possible
    const viaCmd = await commandRuntime.execute("start_workflow", {
      workflowId: id,
      via: "ai",
      utterance,
      aiResult: result,
    });
    if (viaCmd.ok) {
      return {
        ok: true,
        sessionId: viaCmd.message,
        command: viaCmd,
      };
    }
    return this.start(id, { via: "ai", utterance });
  },

  pause(sessionId: string) {
    const s = workflowSessions.get(sessionId);
    if (!s) return { ok: false, error: "session_not_found" };
    if (s.status !== "running" && s.status !== "waiting") {
      return { ok: false, error: "not_pausable" };
    }
    s.status = "paused";
    logSession(s, "info", "Paused");
    workflowSessions.set(s);
    return { ok: true, session: s };
  },

  async resume(sessionId: string, vars?: Record<string, unknown>) {
    const s = workflowSessions.get(sessionId);
    if (!s) return { ok: false, error: "session_not_found" };
    if (vars) Object.assign(s.context.vars, vars);
    if (s.status !== "paused" && s.status !== "waiting") {
      return { ok: false, error: "not_resumable" };
    }
    s.status = "running";
    logSession(s, "info", "Resumed");
    workflowSessions.set(s);
    const live = await advanceSession(sessionId);
    if (live) recordTerminal(live);
    return { ok: true, session: live };
  },

  async restart(sessionId: string) {
    const s = workflowSessions.get(sessionId);
    if (!s) return { ok: false, error: "session_not_found" };
    return this.start(s.definitionId, { ...s.context.vars, restartedFrom: sessionId });
  },

  cancel(sessionId: string) {
    const s = workflowSessions.get(sessionId);
    if (!s) return { ok: false, error: "session_not_found" };
    s.status = "cancelled";
    s.completedAt = new Date().toISOString();
    logSession(s, "warn", "Cancelled");
    workflowSessions.set(s);
    recordTerminal(s);
    return { ok: true, session: s };
  },

  approve(sessionId: string, approved = true) {
    return this.resume(sessionId, { approved });
  },

  /** Replay last history entry by re-starting definition */
  async replay(historyId: string) {
    const hit = workflowHistory.list(100).find((h) => h.id === historyId);
    if (!hit) return { ok: false, error: "history_not_found" };
    return this.start(hit.definitionId, { replayOf: historyId });
  },

  stats() {
    const sessions = workflowSessions.list();
    return {
      version: WORKFLOW_RUNTIME_VERSION,
      definitions: workflowRegistry.list().length,
      active: sessions.filter((s) => s.status === "running").length,
      waiting: sessions.filter((s) => s.status === "waiting").length,
      paused: sessions.filter((s) => s.status === "paused").length,
      completed: workflowHistory.byStatus("completed").length,
      failed: workflowHistory.byStatus("failed").length,
      memoryEstimateKb: Math.round(JSON.stringify(sessions).length / 1024),
    };
  },

  inspectorSnapshot() {
    this.startup();
    return {
      version: WORKFLOW_RUNTIME_VERSION,
      definitions: workflowRegistry.list(),
      sessions: workflowSessions.list(),
      history: workflowHistory.list(40),
      stats: this.stats(),
      eventQueueHint: enterpriseEventBus.recent(8).filter((e) => e.type === "workflow_update"),
    };
  },
};
