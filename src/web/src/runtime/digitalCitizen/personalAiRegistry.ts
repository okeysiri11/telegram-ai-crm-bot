/**
 * Personal AI assistant registry — Sprint 29.1 foundation.
 */

import type { PersonalAiAgent, PersonalAiKind } from "./citizenTypes";

const agents = new Map<string, PersonalAiAgent>();

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

export const personalAiRegistry = {
  clear() {
    agents.clear();
  },

  register(input: {
    kind: PersonalAiKind;
    name: string;
    description?: string;
    ownerCitizenId?: string;
    orgId?: string;
  }): PersonalAiAgent {
    const agent: PersonalAiAgent = {
      id: uid("pai"),
      kind: input.kind,
      name: input.name,
      description: input.description,
      ownerCitizenId: input.ownerCitizenId,
      orgId: input.orgId,
      active: true,
      createdAt: new Date().toISOString(),
    };
    agents.set(agent.id, agent);
    return agent;
  },

  assign(aiId: string, citizenId: string) {
    const cur = agents.get(aiId);
    if (!cur) return null;
    const next = { ...cur, assignedCitizenId: citizenId, active: true };
    agents.set(aiId, next);
    return next;
  },

  unassign(aiId: string) {
    const cur = agents.get(aiId);
    if (!cur) return null;
    const next = { ...cur, assignedCitizenId: undefined };
    agents.set(aiId, next);
    return next;
  },

  get(id: string) {
    return agents.get(id);
  },

  list() {
    return [...agents.values()];
  },

  forCitizen(citizenId: string) {
    return this.list().filter(
      (a) => a.assignedCitizenId === citizenId || a.ownerCitizenId === citizenId,
    );
  },

  byKind(kind: PersonalAiKind) {
    return this.list().filter((a) => a.kind === kind && a.active);
  },
};
