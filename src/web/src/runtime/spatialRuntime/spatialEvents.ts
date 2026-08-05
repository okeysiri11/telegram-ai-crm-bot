/**
 * Spatial events — Sprint 29.4.
 */

import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { SPATIAL_RUNTIME_VERSION, type SpatialEventName } from "./spatialTypes";

const log: {
  id: string;
  name: SpatialEventName;
  at: string;
  entityId?: string;
  subjectId?: string;
  payload: Record<string, unknown>;
}[] = [];

function uid() {
  return `se_${Math.random().toString(36).slice(2, 10)}`;
}

export function publishSpatialEvent(
  name: SpatialEventName,
  payload: Record<string, unknown> = {},
) {
  const entry = {
    id: uid(),
    name,
    at: new Date().toISOString(),
    entityId: payload.entityId ? String(payload.entityId) : undefined,
    subjectId: payload.subjectId ? String(payload.subjectId) : undefined,
    payload,
  };
  log.unshift(entry);
  if (log.length > 300) log.length = 300;

  enterpriseEventBus.publish({
    type: "spatial_runtime_update",
    source: "system",
    payload: {
      stream: "spatial_runtime",
      event: name,
      version: SPATIAL_RUNTIME_VERSION,
      ...payload,
    },
  });
  enterpriseEventBus.publish({
    type: "city_update",
    source: "system",
    payload: { stream: "spatial_runtime", event: name, ...payload },
  });
  return entry;
}

export const spatialEvents = {
  clear() {
    log.length = 0;
  },
  list(limit = 40) {
    return log.slice(0, limit);
  },
  publish: publishSpatialEvent,
};
