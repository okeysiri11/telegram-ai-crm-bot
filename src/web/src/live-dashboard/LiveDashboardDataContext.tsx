import { createContext, useCallback, useContext, useMemo, type ReactNode } from "react";
import { useLiveRuntimeMetrics, type LiveRuntimeMetrics } from "./useLiveRuntimeMetrics";
import { useRuntimeHealth, type RuntimeHealthItem } from "@/shell/enterprise/useRuntimeHealth";
import { useNotificationStore, type AppNotification } from "@/notifications/notificationStore";
import { listActivity, type ActivityEntry } from "@/workspace-engine/activityJournal";
import { useLiveDashboardStore } from "./liveDashboardStore";

type LiveDashboardData = {
  metrics: LiveRuntimeMetrics;
  health: RuntimeHealthItem[];
  refreshHealth: () => void;
  notifications: AppNotification[];
  markAllRead: () => void;
  activity: ActivityEntry[];
  activityFilter: string;
  setActivityFilter: (f: string) => void;
  bumpTick: () => void;
};

const Ctx = createContext<LiveDashboardData | null>(null);

export function LiveDashboardDataProvider({ children }: { children: ReactNode }) {
  const metrics = useLiveRuntimeMetrics();
  const { items: health, refresh } = useRuntimeHealth(15_000);
  const notifications = useNotificationStore((s) => s.items);
  const markAllRead = useNotificationStore((s) => s.markAllRead);
  const activityFilter = useLiveDashboardStore((s) => s.activityFilter);
  const setActivityFilter = useLiveDashboardStore((s) => s.setActivityFilter);
  const bumpTick = useLiveDashboardStore((s) => s.bumpTick);
  const tick = useLiveDashboardStore((s) => s.tick);
  const activity = useMemo(() => {
    void tick;
    return listActivity(8);
  }, [tick]);

  const refreshHealth = useCallback(() => {
    void refresh();
  }, [refresh]);

  const value = useMemo(
    () => ({
      metrics,
      health,
      refreshHealth,
      notifications,
      markAllRead,
      activity,
      activityFilter,
      setActivityFilter,
      bumpTick,
    }),
    [metrics, health, refreshHealth, notifications, markAllRead, activity, activityFilter, setActivityFilter, bumpTick],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useLiveDashboardData(): LiveDashboardData {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useLiveDashboardData requires LiveDashboardDataProvider");
  return ctx;
}
