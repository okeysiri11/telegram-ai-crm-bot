/**
 * Client-side city live status — Sprint 32.3.3.
 * Enriches seed status with notificationStore + light MC probe.
 * No new server architecture.
 */

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/integrations/apiClient";
import { useNotificationStore } from "@/notifications/notificationStore";
import { PLATFORM_BUILDER_API } from "../../platform-builder/types";
import {
  CITY_BUILDINGS,
  CITY_STATUS_SEED,
  type CityBuildingId,
  type CityLiveStatus,
} from "./cityCatalog";

function bumpTone(base: CityLiveStatus, unread: number): CityLiveStatus {
  if (unread >= 4) return { ...base, tone: "alert", notifications: Math.max(base.notifications, unread) };
  if (unread >= 2) return { ...base, tone: base.tone === "idle" ? "active" : base.tone, notifications: Math.max(base.notifications, unread) };
  return base;
}

export function useCityLiveStatus() {
  const items = useNotificationStore((s) => s.items);
  const [mcLinked, setMcLinked] = useState(false);
  const [tick, setTick] = useState(0);

  const refreshMc = useCallback(async () => {
    try {
      const res = await apiFetch(`${PLATFORM_BUILDER_API}/mission-control/status`);
      setMcLinked(res.ok);
    } catch {
      setMcLinked(false);
    }
  }, []);

  useEffect(() => {
    void refreshMc();
    const id = window.setInterval(() => setTick((t) => t + 1), 12_000);
    return () => window.clearInterval(id);
  }, [refreshMc]);

  const unread = items.filter((i) => !i.read).length;

  const statusById: Record<CityBuildingId, CityLiveStatus> = { ...CITY_STATUS_SEED };

  for (const b of CITY_BUILDINGS) {
    const matching = items.filter((n) => {
      const hay = `${n.title} ${n.body} ${n.kind}`.toLowerCase();
      return b.searchTokens.some((t) => hay.includes(t));
    });
    let st = bumpTone(statusById[b.id], matching.filter((m) => !m.read).length || (b.id === "hub" ? unread : 0));
    if (b.id === "mission_control" && mcLinked) {
      st = { ...st, tone: st.tone === "idle" ? "active" : st.tone, processLabel: "MC linked", aiActive: true };
    }
    if (b.id === "ai_team" && tick % 2 === 0) {
      st = { ...st, aiActive: true, tone: st.tone === "idle" ? "active" : st.tone };
    }
    statusById[b.id] = st;
  }

  return { statusById, unread, mcLinked, refreshMc };
}
