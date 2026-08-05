import type { IAgent } from "./interfaces/IAgent.js";
import type { AgentSnapshot } from "./types.js";

/**
 * Registry of all agents — Orchestrator is the only consumer that routes work.
 */
export class AgentRegistry {
  private readonly agents = new Map<string, IAgent>();

  register(agent: IAgent): void {
    if (this.agents.has(agent.id)) {
      throw new Error(`Agent already registered: ${agent.id}`);
    }
    this.agents.set(agent.id, agent);
  }

  get(id: string): IAgent | undefined {
    return this.agents.get(id);
  }

  require(id: string): IAgent {
    const agent = this.agents.get(id);
    if (!agent) throw new Error(`Agent not found: ${id}`);
    return agent;
  }

  list(): readonly IAgent[] {
    return Object.freeze([...this.agents.values()]);
  }

  snapshots(): AgentSnapshot[] {
    return this.list().map((a) => a.snapshot());
  }

  findByCapability(capabilityId: string): IAgent | undefined {
    return this.list().find((a) =>
      a.capabilities().some((c) => c.id === capabilityId),
    );
  }

  clear(): void {
    this.agents.clear();
  }
}
