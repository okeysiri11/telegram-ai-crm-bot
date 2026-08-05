import type {
  AgentCapability,
  AgentHealth,
  AgentLiveStatus,
  AgentSnapshot,
  AgentTaskInput,
  AgentTaskResult,
  ProviderId,
} from "../types.js";

/**
 * Unified agent contract — every agent talks to the Orchestrator only.
 */
export interface IAgent {
  readonly id: string;
  readonly name: string;
  readonly role: string;
  readonly provider: ProviderId;
  readonly memory: string;

  execute(input: AgentTaskInput): Promise<AgentTaskResult>;
  health(): AgentHealth | Promise<AgentHealth>;
  capabilities(): readonly AgentCapability[];
  status(): AgentLiveStatus;
  snapshot(): AgentSnapshot;
}
