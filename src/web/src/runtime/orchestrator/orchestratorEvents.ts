/**
 * Orchestrator events — Sprint 29.8.
 */

import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { ORCHESTRATOR_RUNTIME_VERSION, type OrchestratorEventName } from "./orchestratorTypes";

const log: {
  id: string;
  name: OrchestratorEventName;
  at: string;
  payload: Record<string, unknown>;
}[] = [];

function uid() {
  return `orch_${Math.random().toString(36).slice(2, 10)}`;
}

export function publishOrchestratorEvent(
  name: OrchestratorEventName,
  payload: Record<string, unknown> = {},
) {
  const entry = {
    id: uid(),
    name,
    at: new Date().toISOString(),
    payload,
  };
  log.unshift(entry);
  if (log.length > 400) log.length = 400;

  enterpriseEventBus.publish({
    type: "orchestrator_runtime_update",
    source: "system",
    payload: {
      stream: "orchestrator_runtime",
      event: name,
      version: ORCHESTRATOR_RUNTIME_VERSION,
      ...payload,
    },
  });
  return entry;
}

export const orchestratorEvents = {
  clear() {
    log.length = 0;
  },
  list(limit = 40) {
    return log.slice(0, limit);
  },
  publish: publishOrchestratorEvent,
};
