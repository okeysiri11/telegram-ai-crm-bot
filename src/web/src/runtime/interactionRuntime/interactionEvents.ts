/**
 * Interaction events — Sprint 29.6.
 */

import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { INTERACTION_RUNTIME_VERSION, type InteractionEventName } from "./interactionTypes";

const log: {
  id: string;
  name: InteractionEventName;
  at: string;
  payload: Record<string, unknown>;
}[] = [];

function uid() {
  return `ie_${Math.random().toString(36).slice(2, 10)}`;
}

export function publishInteractionEvent(
  name: InteractionEventName,
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
    type: "interaction_runtime_update",
    source: "system",
    payload: {
      stream: "interaction_runtime",
      event: name,
      version: INTERACTION_RUNTIME_VERSION,
      ...payload,
    },
  });
  enterpriseEventBus.publish({
    type: "city_update",
    source: "system",
    payload: { stream: "interaction_runtime", event: name, ...payload },
  });
  return entry;
}

export const interactionEvents = {
  clear() {
    log.length = 0;
  },
  list(limit = 40) {
    return log.slice(0, limit);
  },
  publish: publishInteractionEvent,
};
