/**
 * Shared Live Enterprise hook — Sprint 32.3.4.
 * One poller + liveUpdates bridge; minimizes duplicate fetches.
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

let sharedSnapshot: LiveEnterpriseSnapshot = emptyLiveSnapshot();
let sharedInflight: Promise<LiveEnterpriseSnapshot> | null = null;
let lastFetchAt = 0;

async function sharedRefresh(notifications: ReturnType<typeof useNotificationStore.getState>["items"]) {
  const now = Date.now();
  if (sharedInflight) return sharedInflight;
  if (now - lastFetchAt < 2_500 && sharedSnapshot.updatedAt !== new Date(0).toISOString()) {
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

  const refresh = useCallback(async () => {
    if (!enabled) return;
    setBusy(true);
    setError(null);
    try {
      const snap = await sharedRefresh(useNotificationStore.getState().items);
      if (mounted.current) setSnapshot(snap);
    } catch (e) {
      if (mounted.current) setError(e instanceof Error ? e.message : "Live refresh failed");
    } finally {
      if (mounted.current) setBusy(false);
    }
  }, [enabled]);

  useEffect(() => {
    mounted.current = true;
    if (!enabled) return;
    liveUpdates.connect();
    void refresh();
    const unsub = liveUpdates.subscribe(() => {
      void refresh();
    });
    const id = window.setInterval(() => {
      liveUpdates.publish("poll");
    }, LIVE_POLL_MS);
    return () => {
      mounted.current = false;
      unsub();
      window.clearInterval(id);
    };
  }, [enabled, refresh]);

  useEffect(() => {
    if (!enabled) return;
    // Notifications change → soft refresh (deduped by sharedRefresh)
    void refresh();
  }, [notifications, enabled, refresh]);

  return { snapshot, busy, error, refresh };
}

export function getSharedLiveSnapshot() {
  return sharedSnapshot;
}
