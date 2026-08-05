/**
 * Sprint 32.1 — Enterprise Multi-Agent Operating System facade.
 * Extends aiAgentRuntime + jobManager. No second orchestrator.
 * n8n = external workflows only.
 */

import { aiAgentRuntime } from "./aiAgentRuntime";
import { DEFAULT_AGENTS, defaultAgentById, type DefaultAgentDef } from "./defaultAgents";
import { jobManager } from "./jobManager";
import { productionRuntime } from "./productionRuntime";
import { launchN8nWorkflow, completeN8nExecution } from "@/enterprise-integrations/n8nBridge";
import type { AgentLifecyclePhase, AiAgentRuntime } from "./types";

export type AgentMessage = {
  id: string;
  fromAgentId: string;
  toAgentId: string;
  type: "delegate" | "result" | "conflict" | "context" | "ping";
  body: string;
  payload?: Record<string, unknown>;
  at: string;
  tenantId: string;
};

export type AgentMemoryKind = "short" | "long" | "vector" | "knowledge" | "company" | "user" | "session";

export type AgentMemoryEntry = {
  id: string;
  agentId: string;
  kind: AgentMemoryKind;
  key: string;
  value: string;
  at: string;
  tenantId: string;
};

export type AgentAuditEvent = {
  id: string;
  agentId: string;
  action: string;
  detail: string;
  at: string;
  tenantId: string;
};

export type CollaborativeRun = {
  id: string;
  title: string;
  leadAgentId: string;
  workerIds: string[];
  status: "running" | "review" | "completed" | "failed";
  results: Record<string, string>;
  conflicts: string[];
  startedAt: string;
  finishedAt?: string;
};

const SESSION_MSG = "ews_agent_os_msg_v1";
const SESSION_MEM = "ews_agent_os_mem_v1";
const SESSION_AUDIT = "ews_agent_os_audit_v1";

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 9)}`;
}

function now() {
  return new Date().toISOString();
}

function readJson<T>(key: string, fallback: T): T {
  try {
    const raw = sessionStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function writeJson(key: string, value: unknown) {
  try {
    sessionStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* ignore */
  }
}

let messages: AgentMessage[] = [];
let memories: AgentMemoryEntry[] = [];
let audit: AgentAuditEvent[] = [];
let collabRuns: CollaborativeRun[] = [];
let hydratedBus = false;

function ensureBus() {
  if (hydratedBus || typeof sessionStorage === "undefined") return;
  messages = readJson(SESSION_MSG, []);
  memories = readJson(SESSION_MEM, []);
  audit = readJson(SESSION_AUDIT, []);
  hydratedBus = true;
}

function persist() {
  if (typeof sessionStorage === "undefined") return;
  writeJson(SESSION_MSG, messages.slice(0, 200));
  writeJson(SESSION_MEM, memories.slice(0, 300));
  writeJson(SESSION_AUDIT, audit.slice(0, 200));
}

function auditLog(agentId: string, action: string, detail: string, tenantId = "org_demo") {
  audit = [{ id: uid("aud"), agentId, action, detail, at: now(), tenantId }, ...audit].slice(0, 200);
  persist();
}

export const agentOs = {
  /** Global registry — catalog + live runtime projection. */
  registry(): Array<DefaultAgentDef & { live?: AiAgentRuntime }> {
    ensureBus();
    return DEFAULT_AGENTS.map((def) => ({
      ...def,
      live: aiAgentRuntime.get(def.id),
    }));
  },

  marketplace(): DefaultAgentDef[] {
    return DEFAULT_AGENTS.filter((a) => !!a.marketplaceTag);
  },

  templates(): DefaultAgentDef[] {
    return DEFAULT_AGENTS.slice();
  },

  getMeta(id: string) {
    return defaultAgentById(id);
  },

  listLive() {
    return aiAgentRuntime.list();
  },

  setPhase(id: string, phase: AgentLifecyclePhase, task?: string | null) {
    aiAgentRuntime.setPhase(id, phase, task);
    auditLog(id, "lifecycle", phase);
  },

  launch(id: string, task: string) {
    aiAgentRuntime.launch(id, task);
    auditLog(id, "launch", task);
  },

  pause(id: string) {
    aiAgentRuntime.pause(id);
    auditLog(id, "pause", "");
  },

  resume(id: string) {
    aiAgentRuntime.resume(id);
    auditLog(id, "resume", "");
  },

  complete(id: string) {
    aiAgentRuntime.complete(id);
    auditLog(id, "complete", "");
  },

  fail(id: string, reason?: string) {
    aiAgentRuntime.fail(id, reason);
    auditLog(id, "fail", reason || "");
  },

  cancel(id: string) {
    aiAgentRuntime.cancel(id);
    auditLog(id, "cancel", "");
  },

  retry(id: string, task?: string) {
    aiAgentRuntime.retry(id, task);
    auditLog(id, "retry", task || "");
  },

  /** Inter-agent messaging (in-memory bus — not a product bus fork). */
  sendMessage(input: Omit<AgentMessage, "id" | "at">): AgentMessage {
    ensureBus();
    const msg: AgentMessage = { ...input, id: uid("am"), at: now() };
    messages = [msg, ...messages].slice(0, 200);
    persist();
    auditLog(input.fromAgentId, "message", `${input.type} → ${input.toAgentId}`);
    return msg;
  },

  inbox(agentId: string): AgentMessage[] {
    return messages.filter((m) => m.toAgentId === agentId);
  },

  listMessages(): AgentMessage[] {
    return messages.slice();
  },

  remember(entry: Omit<AgentMemoryEntry, "id" | "at">): AgentMemoryEntry {
    ensureBus();
    const row: AgentMemoryEntry = { ...entry, id: uid("mem"), at: now() };
    memories = [row, ...memories.filter((m) => !(m.agentId === entry.agentId && m.key === entry.key && m.kind === entry.kind))].slice(
      0,
      300,
    );
    persist();
    return row;
  },

  recall(agentId: string, kind?: AgentMemoryKind): AgentMemoryEntry[] {
    return memories.filter((m) => m.agentId === agentId && (!kind || m.kind === kind));
  },

  sharedContext(tenantId: string): AgentMemoryEntry[] {
    return memories.filter((m) => m.tenantId === tenantId && (m.kind === "company" || m.kind === "session" || m.kind === "knowledge"));
  },

  /**
   * Collaborative multi-agent run: lead plans, workers run parallel, aggregate + conflict check.
   * Execution still goes through Runtime jobs when production=true.
   */
  runCollaborative(input: {
    title: string;
    leadAgentId: string;
    workerIds: string[];
    tenantId?: string;
    viaProduction?: boolean;
    viaN8n?: boolean;
  }): CollaborativeRun {
    ensureBus();
    const tenantId = input.tenantId || "org_demo";
    const run: CollaborativeRun = {
      id: uid("collab"),
      title: input.title,
      leadAgentId: input.leadAgentId,
      workerIds: input.workerIds,
      status: "running",
      results: {},
      conflicts: [],
      startedAt: now(),
    };
    this.setPhase(input.leadAgentId, "planning", input.title);
    this.sendMessage({
      fromAgentId: input.leadAgentId,
      toAgentId: input.leadAgentId,
      type: "context",
      body: `Plan: ${input.title}`,
      tenantId,
    });

    for (const wid of input.workerIds) {
      this.sendMessage({
        fromAgentId: input.leadAgentId,
        toAgentId: wid,
        type: "delegate",
        body: input.title,
        tenantId,
      });
      this.setPhase(wid, "running", input.title);
      const result = `OK · ${wid} · ${input.title}`;
      run.results[wid] = result;
      this.sendMessage({
        fromAgentId: wid,
        toAgentId: input.leadAgentId,
        type: "result",
        body: result,
        tenantId,
      });
      this.remember({
        agentId: wid,
        kind: "short",
        key: `task:${run.id}`,
        value: result,
        tenantId,
      });
      aiAgentRuntime.setAgent(wid, {
        tokensUsed: (aiAgentRuntime.get(wid)?.tokensUsed || 0) + 400,
        costUsd: Number(((aiAgentRuntime.get(wid)?.costUsd || 0) + 0.02).toFixed(4)),
      });
      this.complete(wid);
    }

    // naive conflict: duplicate result bodies
    const values = Object.values(run.results);
    if (new Set(values).size < values.length) {
      run.conflicts.push("duplicate_worker_outputs");
      this.sendMessage({
        fromAgentId: input.leadAgentId,
        toAgentId: input.leadAgentId,
        type: "conflict",
        body: "Duplicate worker outputs",
        tenantId,
      });
    }

    this.setPhase(input.leadAgentId, "review", input.title);

    if (input.viaProduction) {
      productionRuntime.enqueue({
        title: `AgentOS · ${input.title}`,
        queueKind: "task",
        agents: [input.leadAgentId, ...input.workerIds].map((id) => aiAgentRuntime.get(id)?.name || id),
      });
    }

    if (input.viaN8n) {
      const ex = launchN8nWorkflow("n8n_tpl_provider_health", `wf_agentos_${run.id}`);
      completeN8nExecution(ex.id, "success");
    }

    run.status = run.conflicts.length ? "failed" : "completed";
    run.finishedAt = now();
    this.complete(input.leadAgentId);
    auditLog(input.leadAgentId, "collab", `${run.id} · ${run.status}`);
    collabRuns = [run, ...collabRuns].slice(0, 40);
    return run;
  },

  listCollab(): CollaborativeRun[] {
    return collabRuns.slice();
  },

  auditTrail(limit = 50): AgentAuditEvent[] {
    return audit.slice(0, limit);
  },

  /** Owner / monitor snapshot */
  observe() {
    ensureBus();
    const health = aiAgentRuntime.healthSummary();
    const live = aiAgentRuntime.list();
    const counts = jobManager.counts();
    const mon = productionRuntime.monitor();
    const tokens = live.reduce((s, a) => s + (a.tokensUsed || 0), 0);
    const cost = live.reduce((s, a) => s + (a.costUsd || 0), 0);
    return {
      systemOfRecord: "enterprise_runtime",
      orchestrator: "agent_os_facade",
      n8nBusinessLogic: false,
      health,
      runningAgents: live.filter((a) => a.phase === "running" || a.status === "busy"),
      phases: live.reduce(
        (acc, a) => {
          const p = a.phase || "idle";
          acc[p] = (acc[p] || 0) + 1;
          return acc;
        },
        {} as Record<string, number>,
      ),
      jobs: {
        running: counts.running,
        waiting: counts.waiting,
        failed: counts.failed,
        completed: counts.completed,
      },
      queues: mon.queues,
      tokens,
      costUsd: Number(cost.toFixed(4)),
      messages: messages.length,
      memories: memories.length,
      audit: audit.length,
      collab: collabRuns.length,
      latencyHintMs: 120 + (health.busy || 0) * 15,
    };
  },

  resetBus() {
    messages = [];
    memories = [];
    audit = [];
    collabRuns = [];
    hydratedBus = true;
    persist();
    aiAgentRuntime.reset();
  },
};

export type AgentOsObserve = ReturnType<typeof agentOs.observe>;
