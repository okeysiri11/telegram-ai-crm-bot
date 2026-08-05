import { liveUpdates, type LiveUpdate } from "../../workspace/realtime/liveUpdates";
import { useLiveDashboardStore } from "./liveDashboardStore";
import { useNotificationStore } from "@/notifications/notificationStore";
import { useEffect, useRef } from "react";

export type DashboardBusEvent =
  | { type: "notifications" }
  | { type: "jobs" }
  | { type: "agent_execution" }
  | { type: "runtime_status" }
  | { type: "errors" }
  | { type: "background_tasks" }
  | { type: "refresh"; source: LiveUpdate["source"] };

type BusListener = (e: DashboardBusEvent) => void;

const listeners = new Set<BusListener>();
let notifBound = false;
let prevUnread = -1;
let prevJobs = -1;

function emit(e: DashboardBusEvent) {
  listeners.forEach((l) => l(e));
  useLiveDashboardStore.getState().bumpTick();
}

export const dashboardEventBus = {
  subscribe(listener: BusListener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  publish(e: DashboardBusEvent) {
    emit(e);
  },
  /** Bridge liveUpdates + notification store into dashboard ticks. */
  connect() {
    liveUpdates.connect();
    const unsubLive = liveUpdates.subscribe((u) => {
      emit({ type: "refresh", source: u.source });
      if (u.source === "notification_center") emit({ type: "notifications" });
      if (u.source === "event_bus") emit({ type: "agent_execution" });
    });
    if (!notifBound) {
      notifBound = true;
      // poll notification deltas lightly via interval (store has no subscribe API beyond zustand)
    }
    return () => {
      unsubLive();
    };
  },
};

/** Hook: keep dashboard widgets live via event bus + notification deltas. */
export function useDashboardEventBus() {
  const bumpTick = useLiveDashboardStore((s) => s.bumpTick);
  const items = useNotificationStore((s) => s.items);
  const bound = useRef(false);

  useEffect(() => {
    if (bound.current) return;
    bound.current = true;
    const cleanup = dashboardEventBus.connect();
    const unsub = dashboardEventBus.subscribe(() => {
      /* tick already bumped in emit */
    });
    const poll = window.setInterval(() => {
      liveUpdates.publish("poll");
      emit({ type: "runtime_status" });
    }, 15_000);
    return () => {
      cleanup();
      unsub();
      window.clearInterval(poll);
      bound.current = false;
    };
  }, []);

  useEffect(() => {
    const unread = items.filter((i) => !i.read).length;
    const jobs = items.filter((i) => i.kind === "job" || i.kind === "workflow" || i.kind === "task").length;
    const errors = items.filter((i) => i.kind === "error").length;
    if (prevUnread >= 0 && unread !== prevUnread) {
      emit({ type: "notifications" });
    }
    if (prevJobs >= 0 && jobs !== prevJobs) {
      emit({ type: "jobs" });
      emit({ type: "background_tasks" });
    }
    if (errors > 0 && prevUnread >= 0) {
      emit({ type: "errors" });
    }
    prevUnread = unread;
    prevJobs = jobs;
    bumpTick();
  }, [items, bumpTick]);
}
