export const AI_OS_VERSION = "9.4.0";
export const AI_OS_API = "/api/ai-os/v1";
export const AI_OS_PATH = "src/web/ai-os";

export type AgentInfo = {
  agentId: string;
  name: string;
  role: string;
  status: string;
  load: number;
  capabilities: string[];
  cost: number;
  speed: number;
  memory: number;
  models: string[];
};

export type ExecutiveDashboardData = {
  title: string;
  version: string;
  activeCount: number;
  agentsTotal: number;
  queueBus: number;
  queuePriority: number;
  cost: number;
  latencyMsAvg: number;
  agents: AgentInfo[];
  taskHistory: { taskId?: string; goal?: string; status?: string; name?: string; ok?: boolean }[];
  errors: { error: string }[];
};
