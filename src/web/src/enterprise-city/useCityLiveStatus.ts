/**
 * Client-side city live status — Sprint 32.3.3 + Live Ops 32.3.4.
 * Enriches seed status with notifications + shared Live Enterprise snapshot.
 * No new server architecture.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useNotificationStore } from "@/notifications/notificationStore";
import { useLiveEnterprise } from "@/live-ops";
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
  const { snapshot, refresh } = useLiveEnterprise(true);
  const [pulse, setPulse] = useState(0);

  useEffect(() => {
    const id = window.setInterval(() => setPulse((p) => p + 1), 4_000);
    return () => window.clearInterval(id);
  }, []);

  const refreshMc = useCallback(async () => {
    await refresh();
  }, [refresh]);

  const unread = items.filter((i) => !i.read).length;
  const active = snapshot.activeModules;

  const statusById = useMemo(() => {
    const out: Record<CityBuildingId, CityLiveStatus> = { ...CITY_STATUS_SEED };
    for (const b of CITY_BUILDINGS) {
      const matching = items.filter((n) => {
        const hay = `${n.title} ${n.body} ${n.kind}`.toLowerCase();
        return b.searchTokens.some((t) => hay.includes(t));
      });
      const feedHits = snapshot.activity.filter((a) => {
        const hay = `${a.title} ${a.detail} ${a.moduleHint || ""}`.toLowerCase();
        return b.searchTokens.some((t) => hay.includes(t));
      }).length;

      let st = bumpTone(out[b.id], matching.filter((m) => !m.read).length || (b.id === "hub" ? unread : 0));
      if (feedHits > 0) {
        st = {
          ...st,
          tone: feedHits > 2 ? "busy" : "active",
          notifications: Math.max(st.notifications, feedHits),
          processLabel: snapshot.activity.find((a) => a.moduleHint && b.searchTokens.includes(a.moduleHint))?.title || st.processLabel,
        };
      }
      if (b.id === "mission_control" && snapshot.mcOk) {
        st = { ...st, tone: st.tone === "idle" ? "active" : st.tone, processLabel: "MC live", aiActive: true };
      }
      if (b.id === "ai_team" || b.id === "concierge") {
        st = {
          ...st,
          aiActive: true,
          tone: pulse % 2 === 0 ? "busy" : "active",
          processLabel: snapshot.aiOps.running[0] || st.processLabel,
        };
      }
      if (active.some((m) => b.searchTokens.includes(m) || b.id.includes(m))) {
        st = { ...st, tone: st.tone === "idle" ? "active" : st.tone, aiActive: st.aiActive || mIsAi(b.id) };
      }
      const health = snapshot.health.find((h) =>
        (b.id === "crm" && h.id === "crm") ||
        (b.id === "analytics" && h.id === "analytics") ||
        (b.id === "documents" && h.id === "documents") ||
        (b.id === "knowledge" && h.id === "knowledge") ||
        (b.id === "mission_control" && h.id === "mission_control") ||
        (b.id === "ai_team" && h.id === "ai_core"),
      );
      if (health && !health.ok) {
        st = { ...st, tone: "alert", processLabel: "Health check" };
      }
      out[b.id] = st;
    }
    return out;
  }, [items, snapshot, unread, active, pulse]);

  return { statusById, unread, mcLinked: snapshot.mcOk, refreshMc, activeModules: active };
}

function mIsAi(id: CityBuildingId) {
  return id === "ai_team" || id === "concierge" || id === "analytics";
}
