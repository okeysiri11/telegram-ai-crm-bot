/**
 * AI Agents as runtime entities — Sprint 28.1 / 30.5 / 32.1 AgentOS SoR.
 * Bootstraps canonical DEFAULT_AGENTS + production studio specialists.
 * No parallel orchestrator — Job Manager owns tasks.
 */

import { DEFAULT_AGENTS } from "./defaultAgents";
import { PRODUCTION_STUDIOS } from "@/ai-production-studio/productionCatalog";
import type { AgentLifecyclePhase, AiAgentRuntime, HealthLevel } from "./types";

type Listener = (agents: AiAgentRuntime[]) => void;

const listeners = new Set<Listener>();
let agents: AiAgentRuntime[] = bootstrapAgents();

function now() {
  return new Date().toISOString();
}

export function phaseToStatus(phase: AgentLifecyclePhase): AiAgentRuntime["status"] {
  switch (phase) {
    case "idle":
    case "completed":
    case "cancelled":
      return "idle";
    case "planning":
    case "running":
    case "review":
      return "busy";
    case "waiting":
    case "paused":
    case "retry":
      return "waiting";
    case "failed":
      return "error";
    default:
      return "idle";
  }
}

function bootstrapAgents(): AiAgentRuntime[] {
  const t = now();
  const byId = new Map<string, AiAgentRuntime>();

  DEFAULT_AGENTS.forEach((def, i) => {
    const status: AiAgentRuntime["status"] =
      i % 5 === 0 ? "busy" : i % 7 === 0 ? "waiting" : "idle";
    const phase: AgentLifecyclePhase =
      status === "busy" ? "running" : status === "waiting" ? "waiting" : "idle";
    byId.set(def.id, {
      id: def.id,
      name: def.nameRu,
      status,
      phase,
      role: def.role,
      version: def.version,
      permissions: def.permissions,
      task: status === "busy" ? `Задача · ${def.nameRu}` : status === "waiting" ? "В очереди" : null,
      queueDepth: status === "waiting" || status === "busy" ? (i % 3) + 1 : 0,
      memoryMb: 64 + (i % 5) * 12,
      workflow: status === "busy" ? "agent_os" : null,
      health: (status === "busy" ? "warning" : "healthy") as HealthLevel,
      tokensUsed: 0,
      costUsd: 0,
      tenantId: "org_demo",
      updatedAt: t,
    });
  });

  for (const s of PRODUCTION_STUDIOS) {
    for (const name of s.aiAgents) {
      const id = `agent_${name.toLowerCase().replace(/\s+/g, "_")}`;
      if (byId.has(id)) continue;
      byId.set(id, {
        id,
        name,
        status: "idle",
        phase: "idle",
        role: "production",
        version: "1.0.0",
        permissions: ["ai_agents", "production"],
        task: null,
        queueDepth: 0,
        memoryMb: 48,
        workflow: null,
        health: "healthy",
        tokensUsed: 0,
        costUsd: 0,
        tenantId: "org_demo",
        updatedAt: t,
      });
    }
  }

  ["Concierge", "Ops Copilot", "CRM Copilot"].forEach((name) => {
    const id = `agent_${name.toLowerCase().replace(/\s+/g, "_")}`;
    if (!byId.has(id)) {
      byId.set(id, {
        id,
        name,
        status: "idle",
        phase: "idle",
        role: "support",
        version: "1.0.0",
        permissions: ["ai_agents"],
        task: null,
        queueDepth: 0,
        memoryMb: 56,
        workflow: null,
        health: "healthy",
        tokensUsed: 0,
        costUsd: 0,
        tenantId: "org_demo",
        updatedAt: t,
      });
    }
  });

  return [...byId.values()];
}

function emit() {
  listeners.forEach((l) => l(agents.slice()));
}

export const aiAgentRuntime = {
  subscribe(listener: Listener) {
    listeners.add(listener);
    listener(agents.slice());
    return () => {
      listeners.delete(listener);
    };
  },

  list() {
    return agents.slice();
  },

  get(id: string) {
    return agents.find((a) => a.id === id);
  },

  defaultAgents() {
    return agents.filter((a) => DEFAULT_AGENTS.some((d) => d.id === a.id));
  },

  activeCount() {
    return agents.filter((a) => a.status === "busy" || a.status === "waiting").length;
  },

  healthSummary() {
    const list = agents;
    return {
      total: list.length,
      healthy: list.filter((a) => a.health === "healthy").length,
      warning: list.filter((a) => a.health === "warning").length,
      critical: list.filter((a) => a.health === "critical").length,
      offline: list.filter((a) => a.health === "offline" || a.status === "offline").length,
      busy: list.filter((a) => a.status === "busy").length,
    };
  },

  setPhase(id: string, phase: AgentLifecyclePhase, task?: string | null) {
    agents = agents.map((a) =>
      a.id === id
        ? {
            ...a,
            phase,
            status: phaseToStatus(phase),
            task: task === undefined ? a.task : task,
            workflow: phase === "idle" || phase === "completed" || phase === "cancelled" ? null : a.workflow || "agent_os",
            health:
              phase === "failed"
                ? "critical"
                : phase === "running" || phase === "planning"
                  ? "warning"
                  : "healthy",
            updatedAt: now(),
          }
        : a,
    );
    emit();
  },

  launch(id: string, taskTitle: string) {
    this.setPhase(id, "planning", taskTitle);
    this.setPhase(id, "running", taskTitle);
  },

  pause(id: string) {
    this.setPhase(id, "paused");
  },

  resume(id: string) {
    this.setPhase(id, "running");
  },

  complete(id: string) {
    this.setPhase(id, "completed", null);
    this.setPhase(id, "idle", null);
  },

  fail(id: string, reason?: string) {
    this.setPhase(id, "failed", reason || "error");
  },

  cancel(id: string) {
    this.setPhase(id, "cancelled", null);
    this.setPhase(id, "idle", null);
  },

  retry(id: string, taskTitle?: string) {
    this.setPhase(id, "retry", taskTitle || "retry");
    this.setPhase(id, "running", taskTitle || "retry");
  },

  tick() {
    agents = agents.map((a, i) => {
      if (a.status === "offline") return a;
      if (i % 4 === 0 && a.status === "idle") {
        return {
          ...a,
          status: "busy",
          phase: "running",
          task: `Task · ${a.name}`,
          queueDepth: 1,
          workflow: a.workflow || "agent_os",
          health: "warning",
          memoryMb: a.memoryMb + 2,
          updatedAt: now(),
        };
      }
      if (a.status === "busy" && i % 3 === 0) {
        return {
          ...a,
          status: "idle",
          phase: "idle",
          task: null,
          queueDepth: 0,
          workflow: null,
          health: "healthy",
          memoryMb: Math.max(32, a.memoryMb - 4),
          updatedAt: now(),
        };
      }
      if (a.status === "busy") {
        return { ...a, memoryMb: a.memoryMb + (i % 2), updatedAt: now() };
      }
      return a;
    });
    emit();
  },

  setAgent(id: string, patch: Partial<AiAgentRuntime>) {
    agents = agents.map((a) => (a.id === id ? { ...a, ...patch, updatedAt: now() } : a));
    emit();
  },

  /** Test / sprint reset — re-bootstrap from catalog. */
  reset() {
    agents = bootstrapAgents();
    emit();
  },
};
