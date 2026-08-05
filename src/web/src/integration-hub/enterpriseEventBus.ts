/**
 * Typed enterprise event bus — Sprint 28.0.
 * Thin wrapper over liveUpdates + local listeners. No second realtime stack.
 */

import { liveUpdates } from "../../workspace/realtime/liveUpdates";
import type { EnterpriseEvent, EnterpriseEventType, OsSurfaceId } from "./types";

type Listener = (event: EnterpriseEvent) => void;

const listeners = new Set<Listener>();
const recent: EnterpriseEvent[] = [];
const MAX_RECENT = 40;
let liveBound = false;
/** Prevent liveUpdates → hub → liveUpdates recursion. */
let bridgingFromLive = false;

function pushRecent(event: EnterpriseEvent) {
  recent.unshift(event);
  if (recent.length > MAX_RECENT) recent.length = MAX_RECENT;
}

export const enterpriseEventBus = {
  publish(partial: Omit<EnterpriseEvent, "at"> & { at?: string }) {
    const event: EnterpriseEvent = {
      ...partial,
      at: partial.at || new Date().toISOString(),
    };
    pushRecent(event);
    listeners.forEach((l) => l(event));
    if (
      !bridgingFromLive &&
      (event.type === "job_update" || event.type === "notification" || event.type === "ai_request")
    ) {
      liveUpdates.publish(event.type === "notification" ? "notification_center" : "event_bus");
    }
    return event;
  },

  subscribe(listener: Listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },

  subscribeType(type: EnterpriseEventType, listener: Listener) {
    return this.subscribe((e) => {
      if (e.type === type) listener(e);
    });
  },

  recent(limit = 12): EnterpriseEvent[] {
    return recent.slice(0, limit);
  },

  /** Bind once to liveUpdates so poll/WS also fans into hub listeners. */
  connectLiveBridge() {
    if (liveBound) return;
    liveBound = true;
    liveUpdates.connect();
    liveUpdates.subscribe((update) => {
      bridgingFromLive = true;
      try {
        this.publish({
          type: "runtime_update",
          source: "system",
          payload: { liveSource: update.source, widgetIds: update.widgetIds },
        });
      } finally {
        bridgingFromLive = false;
      }
    });
  },

  navigate(path: string, source: OsSurfaceId | "hub" = "hub") {
    return this.publish({ type: "navigate", source, path, payload: { path } });
  },

  openModule(path: string, source: OsSurfaceId | "hub", extra?: Record<string, unknown>) {
    return this.publish({ type: "open_module", source, path, payload: { path, ...extra } });
  },

  openCityBuilding(buildingId: string, path: string) {
    return this.publish({
      type: "open_city_building",
      source: "city",
      path,
      payload: { buildingId, path },
    });
  },

  openProduction(studio?: string, tab?: string) {
    const path = studio
      ? `/production-studio?studio=${studio}`
      : tab
        ? `/production-studio?tab=${tab}`
        : "/production-studio";
    return this.publish({
      type: "open_production",
      source: "production",
      path,
      payload: { studio, tab },
    });
  },
};
