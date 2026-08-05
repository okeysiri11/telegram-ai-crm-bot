/**
 * Intelligence events — Sprint 29.7 (advisory stream only).
 */

import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { INTELLIGENCE_RUNTIME_VERSION, type IntelligenceEventName } from "./intelligenceTypes";

const log: {
  id: string;
  name: IntelligenceEventName;
  at: string;
  payload: Record<string, unknown>;
}[] = [];

function uid() {
  return `intel_${Math.random().toString(36).slice(2, 10)}`;
}

export function publishIntelligenceEvent(
  name: IntelligenceEventName,
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
    type: "intelligence_runtime_update",
    source: "system",
    payload: {
      stream: "intelligence_runtime",
      event: name,
      version: INTELLIGENCE_RUNTIME_VERSION,
      advisory: true,
      ...payload,
    },
  });
  return entry;
}

export const intelligenceEvents = {
  clear() {
    log.length = 0;
  },
  list(limit = 40) {
    return log.slice(0, limit);
  },
  publish: publishIntelligenceEvent,
};
