import type { AgentInfo, ExecutiveDashboardData } from "../types";
import { AI_OS_VERSION } from "../types";

const AGENTS: AgentInfo[] = [
  { agentId: "agent_director", name: "AI Director", role: "executive", status: "idle", load: 0.1, capabilities: ["plan", "delegate", "merge"], cost: 0.01, speed: 20, memory: 1024, models: ["gpt-executive"] },
  { agentId: "agent_sales", name: "Sales Agent", role: "sales", status: "idle", load: 0.2, capabilities: ["qualify", "crm"], cost: 0.003, speed: 50, memory: 256, models: ["gpt-sales"] },
  { agentId: "agent_ops", name: "Ops Copilot", role: "operations", status: "busy", load: 0.55, capabilities: ["triage", "workflow"], cost: 0.002, speed: 55, memory: 256, models: ["gpt-ops"] },
  { agentId: "agent_legal", name: "Legal Case Agent", role: "legal", status: "idle", load: 0.15, capabilities: ["review", "compliance"], cost: 0.004, speed: 35, memory: 256, models: ["gpt-legal"] },
  { agentId: "agent_finance", name: "Finance CFO Agent", role: "finance", status: "idle", load: 0.2, capabilities: ["invoice", "forecast"], cost: 0.004, speed: 35, memory: 256, models: ["gpt-cfo"] },
  { agentId: "agent_research", name: "Research Agent", role: "knowledge", status: "idle", load: 0.3, capabilities: ["search", "rag"], cost: 0.002, speed: 60, memory: 256, models: ["gpt-research"] },
  { agentId: "agent_critic", name: "Critic Agent", role: "quality", status: "idle", load: 0.1, capabilities: ["critique", "vote"], cost: 0.002, speed: 70, memory: 256, models: ["gpt-critic"] },
  { agentId: "agent_builder", name: "Builder Agent", role: "engineering", status: "idle", load: 0.25, capabilities: ["codegen", "test"], cost: 0.005, speed: 30, memory: 256, models: ["gpt-code"] },
];

export function buildExecutiveDashboard(): ExecutiveDashboardData {
  return {
    title: "AI Executive Dashboard",
    version: AI_OS_VERSION,
    activeCount: AGENTS.filter((a) => a.status === "busy").length,
    agentsTotal: AGENTS.length,
    queueBus: 12,
    queuePriority: 2,
    cost: 0.042,
    latencyMsAvg: 18.5,
    agents: AGENTS,
    taskHistory: [
      { taskId: "exec_demo", goal: "Weekly ops report", status: "completed" },
      { name: "demo_dag", ok: true },
    ],
    errors: [],
  };
}

export const agentRegistry = {
  list(): AgentInfo[] {
    return [...AGENTS];
  },
};
