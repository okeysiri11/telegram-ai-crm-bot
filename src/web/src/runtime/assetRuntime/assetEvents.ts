/**
 * Asset events + EventBus — Sprint 29.3.
 */

import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { ASSET_RUNTIME_VERSION, type AssetEventName } from "./assetTypes";

const log: { id: string; name: AssetEventName; assetId: string; at: string; payload: Record<string, unknown> }[] =
  [];

function uid() {
  return `ae_${Math.random().toString(36).slice(2, 10)}`;
}

export function publishAssetEvent(
  name: AssetEventName,
  assetId: string,
  payload: Record<string, unknown> = {},
) {
  const entry = {
    id: uid(),
    name,
    assetId,
    at: new Date().toISOString(),
    payload,
  };
  log.unshift(entry);
  if (log.length > 300) log.length = 300;

  enterpriseEventBus.publish({
    type: "asset_runtime_update",
    source: "system",
    payload: {
      stream: "asset_runtime",
      event: name,
      assetId,
      version: ASSET_RUNTIME_VERSION,
      ...payload,
    },
  });
  enterpriseEventBus.publish({
    type: "city_update",
    source: "system",
    payload: { stream: "asset_runtime", event: name, assetId },
  });
  return entry;
}

export const assetEvents = {
  clear() {
    log.length = 0;
  },
  list(limit = 40) {
    return log.slice(0, limit);
  },
  publish: publishAssetEvent,
};
