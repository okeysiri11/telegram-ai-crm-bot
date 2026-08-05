/**
 * City visualization events — Sprint 29.5.
 */

import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { CITY_VIS_VERSION, type CityVisEventName } from "./cityVisualizationTypes";

const log: {
  id: string;
  name: CityVisEventName;
  at: string;
  subjectId?: string;
  payload: Record<string, unknown>;
}[] = [];

function uid() {
  return `cve_${Math.random().toString(36).slice(2, 10)}`;
}

export function publishCityVisEvent(
  name: CityVisEventName,
  payload: Record<string, unknown> = {},
) {
  const entry = {
    id: uid(),
    name,
    at: new Date().toISOString(),
    subjectId: payload.subjectId ? String(payload.subjectId) : undefined,
    payload,
  };
  log.unshift(entry);
  if (log.length > 400) log.length = 400;

  enterpriseEventBus.publish({
    type: "city_visualization_update",
    source: "system",
    payload: {
      stream: "city_visualization",
      event: name,
      version: CITY_VIS_VERSION,
      ...payload,
    },
  });
  enterpriseEventBus.publish({
    type: "city_update",
    source: "system",
    payload: { stream: "city_visualization", event: name, ...payload },
  });
  return entry;
}

export const cityVisualizationEvents = {
  clear() {
    log.length = 0;
  },
  list(limit = 40) {
    return log.slice(0, limit);
  },
  publish: publishCityVisEvent,
};
