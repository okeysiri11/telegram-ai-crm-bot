/**
 * Shared Live Enterprise hook — Sprint 32.3.4 / EP-07 production hardening.
 * Singleton poller + liveUpdates bridge; minimizes duplicate fetches & intervals.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useNotificationStore } from "@/notifications/notificationStore";
import { liveUpdates } from "../../workspace/realtime/liveUpdates";
import { LIVE_POLL_MS } from "./liveEnterpriseCatalog";
import {
  emptyLiveSnapshot,
  fetchLiveEnterpriseSnapshot,
  type LiveEnterpriseSnapshot,
} from "./fetchLiveEnterprise";
import {
  LIVE_FETCH_DEDUPE_MS,
  isDocumentHidden,
  prodLog,
  sanitizeErrorMessage,
} from "@/production";

let sharedSnapshot: LiveEnterpriseSnapshot = emptyLiveSnapshot();
let sharedInflight: Promise<LiveEnterpriseSnapshot> | null = null;
let lastFetchAt = 0;

let pollerRefCount = 0;
let pollerId: number | null = null;
let visibilityBound = false;

function onVisibility() {
  if (!isDocumentHidden()) {
    liveUpdates.publish("poll");
  }
}

function acquireSharedPoller() {
  pollerRefCount += 1;
  if (pollerId != null) return;
  liveUpdates.connect();
  pollerId = window.setInterval(() => {
    if (isDocumentHidden()) return;
    liveUpdates.publish("poll");
  }, LIVE_POLL_MS);
  if (!visibilityBound && typeof document !== "undefined") {
    document.addEventListener("visibilitychange", onVisibility);
    visibilityBound = true;
  }
  prodLog("debug", "live_poller_acquired", { pollerRefCount, pollMs: LIVE_POLL_MS });
}

function releaseSharedPoller() {
  pollerRefCount = Math.max(0, pollerRefCount - 1);
  if (pollerRefCount > 0) return;
  if (pollerId != null) {
    window.clearInterval(pollerId);
    pollerId = null;
  }
  if (visibilityBound && typeof document !== "undefined") {
    document.removeEventListener("visibilitychange", onVisibility);
    visibilityBound = false;
  }
  prodLog("debug", "live_poller_released");
}

async function sharedRefresh(notifications: ReturnType<typeof useNotificationStore.getState>["items"]) {
  const now = Date.now();
  if (sharedInflight) return sharedInflight;
  if (now - lastFetchAt < LIVE_FETCH_DEDUPE_MS && sharedSnapshot.updatedAt !== new Date(0).toISOString()) {
    return sharedSnapshot;
  }
  sharedInflight = fetchLiveEnterpriseSnapshot(notifications)
    .then((snap) => {
      sharedSnapshot = snap;
      lastFetchAt = Date.now();
      return snap;
    })
    .finally(() => {
      sharedInflight = null;
    });
  return sharedInflight;
}

export function useLiveEnterprise(enabled = true) {
  const notifications = useNotificationStore((s) => s.items);
  const [snapshot, setSnapshot] = useState<LiveEnterpriseSnapshot>(sharedSnapshot);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mounted = useRef(true);
  const notifLen = notifications.length;

  const refresh = useCallback(async () => {
    if (!enabled) return;
    setBusy((b) => (b ? b : true));
    setError(null);
    try {
      const snap = await sharedRefresh(useNotificationStore.getState().items);
      if (mounted.current) {
        setSnapshot((prev) => (prev.updatedAt === snap.updatedAt ? prev : snap));
      }
    } catch (e) {
      const msg = sanitizeErrorMessage(e instanceof Error ? e.message : "Live refresh failed");
      prodLog("warn", "live_refresh_failed", { message: msg });
      if (mounted.current) setError(msg);
    } finally {
      if (mounted.current) setBusy(false);
    }
  }, [enabled]);

  useEffect(() => {
    mounted.current = true;
    if (!enabled) return;
    acquireSharedPoller();
    void refresh();
    const unsub = liveUpdates.subscribe(() => {
      if (isDocumentHidden()) return;
      void refresh();
    });
    return () => {
      mounted.current = false;
      unsub();
      releaseSharedPoller();
    };
  }, [enabled, refresh]);

  useEffect(() => {
    if (!enabled) return;
    // Soft refresh when notification count changes (deduped)
    void refresh();
  }, [notifLen, enabled, refresh]);

  return { snapshot, busy, error, refresh };
}

export function getSharedLiveSnapshot() {
  return sharedSnapshot;
}

/** Test / diagnostics hook — current poller refcount. */
export function __livePollerRefCount() {
  return pollerRefCount;
}
