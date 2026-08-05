/**
 * Client-side city live status — Sprint 32.3.3 + Live Ops 32.3.4.
 * Enriches seed status with notifications + shared Live Enterprise snapshot.
 * No new server architecture.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useNotificationStore } from "@/notifications/notificationStore";
import { useLiveEnterprise } from "@/live-ops";
import { productionRuntime } from "@/enterprise-runtime/productionRuntime";
import { businessNetworkEngine, EBN_HOME_PROFILE_ID } from "@/runtime/businessNetwork";
import { digitalCitizenEngine, EDC_CITIZEN_OWNER } from "@/runtime/digitalCitizen";
import { lifeEngine } from "@/runtime/lifeEngine";
import { assetRuntime } from "@/runtime/assetRuntime";
import { spatialRuntime } from "@/runtime/spatialRuntime";
import { cityVisualizationRuntime } from "@/runtime/cityVisualization";
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
    // EP-07: align city visual pulse with live poll cadence (less CPU on long sessions)
    const id = window.setInterval(() => setPulse((p) => p + 1), 12_000);
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
      if (b.id === "ai_team" || b.id === "concierge" || b.id === "ai_studio") {
        st = {
          ...st,
          aiActive: true,
          tone: pulse % 2 === 0 ? "busy" : "active",
          processLabel: snapshot.aiOps.running[0] || st.processLabel,
        };
      }
      if (b.id === "plaza") {
        st = { ...st, aiActive: true, tone: "active", processLabel: "City navigation" };
      }
      // Sprint 28.2 — Production district occupancy from Production Runtime queues
      if (b.district === "production" || b.id.startsWith("prod_") || b.id === "production") {
        const mon = productionRuntime.monitor();
        const gen = mon.queues.generation.length;
        const render = mon.queues.render.length;
        const pub = mon.queues.publishing.length;
        const total = gen + render + pub + mon.queues.task.length;
        if (b.id === "prod_render" && render > 0) {
          st = { ...st, tone: "busy", tasks: render, aiActive: true, processLabel: `Render Q ${render}` };
        } else if (b.id === "prod_publish" && pub > 0) {
          st = { ...st, tone: "busy", tasks: pub, processLabel: `Publish Q ${pub}` };
        } else if ((b.id === "prod_image" || b.id === "prod_video" || b.id === "prod_reels") && gen > 0) {
          st = { ...st, tone: "busy", tasks: Math.max(st.tasks, gen), aiActive: true, processLabel: `Gen Q ${gen}` };
        } else if (b.id === "production" && total > 0) {
          st = { ...st, tone: total > 6 ? "busy" : "active", tasks: total, aiActive: true, processLabel: `Queues ${total}` };
        } else if (b.id === "prod_analytics") {
          st = {
            ...st,
            tone: "active",
            processLabel: `ETA ${mon.analytics.estimatedClearSec}s`,
            aiActive: mon.agentsActive > 0,
          };
        }
      }
      // Sprint 29.3 — Asset inventory enriches building process label
      try {
        assetRuntime.startup();
        const assets = assetRuntime.assetsByBuilding(b.id);
        if (assets.length > 0) {
          const maint = assets.filter((a) => a.status === "maintenance").length;
          const avail = assets.filter((a) => a.available).length;
          st = {
            ...st,
            tasks: Math.max(st.tasks, assets.length),
            tone: maint > 0 ? "alert" : st.tone === "idle" ? "active" : st.tone,
            processLabel:
              maint > 0
                ? `Assets ${assets.length} · ${maint} maint`
                : st.processLabel.includes("present") || st.processLabel.includes("meeting")
                  ? st.processLabel
                  : `Assets ${assets.length} · ${avail} free`,
          };
        }
      } catch {
        /* optional */
      }
      // Sprint 29.4 — Spatial twin district tag when idle process label
      try {
        spatialRuntime.startup();
        const entity = spatialRuntime.list("building").find((e) => e.cityBuildingId === b.id);
        if (entity?.cityDistrictId && st.tone === "idle" && !st.processLabel) {
          st = { ...st, processLabel: `District ${entity.cityDistrictId}` };
        }
      } catch {
        /* optional */
      }
      // Sprint 29.2 — Life Engine occupancy drives building tone (real runtime)
      try {
        lifeEngine.startup();
        const [occ] = lifeEngine.occupancy(b.id);
        if (occ && occ.occupants.length > 0) {
          st = {
            ...st,
            tone: occ.meetingCount > 0 || occ.occupants.length > 6 ? "busy" : "active",
            tasks: Math.max(st.tasks, occ.occupants.length),
            notifications: Math.max(st.notifications, occ.meetingCount),
            processLabel: occ.activityLabel,
            aiActive: st.aiActive || occ.occupants.some((o) => o.kind === "ai"),
          };
        }
      } catch {
        /* life engine optional */
      }
      // Sprint 29.5 — Visualization Runtime consolidates visual status for City clients
      try {
        cityVisualizationRuntime.startup();
        const vs = cityVisualizationRuntime.buildingState(b.id);
        if (vs) {
          const toneMap = {
            idle: "idle",
            active: "active",
            busy: "busy",
            alert: "alert",
            offline: "idle",
            maintenance: "alert",
          } as const;
          st = {
            ...st,
            tone: toneMap[vs.status] || st.tone,
            tasks: Math.max(st.tasks, vs.occupancy + vs.meetingCount),
            processLabel:
              vs.processLabel ||
              (vs.meetingCount > 0
                ? `Meetings ${vs.meetingCount}`
                : vs.occupancy > 0
                  ? `${vs.occupancy} present`
                  : st.processLabel),
          };
        }
      } catch {
        /* optional */
      }
      if (b.id === "digital_citizens" || b.id === "hr") {
        digitalCitizenEngine.startup();
        const facade = digitalCitizenEngine.cityFacade(EDC_CITIZEN_OWNER);
        const online = digitalCitizenEngine.presenceSnapshot().filter((p) =>
          ["online", "busy", "meeting", "working"].includes(p.status),
        ).length;
        if (facade) {
          st = {
            ...st,
            tone: online > 0 ? "active" : st.tone,
            tasks: Math.max(st.tasks, online),
            aiActive: facade.aiAssignmentIds.length > 0,
            processLabel: `${facade.presence} · ${online} present`,
          };
        }
      }
      if (b.id === "business_network" || b.id === "hub") {
        businessNetworkEngine.startup();
        const facade = businessNetworkEngine.cityFacade(EBN_HOME_PROFILE_ID);
        if (facade) {
          st = {
            ...st,
            tone: facade.relationshipCount > 0 ? "active" : st.tone,
            tasks: Math.max(st.tasks, facade.relationshipCount),
            processLabel:
              b.id === "business_network"
                ? `Trust ${facade.trustLevel} · ${facade.relationshipCount} links`
                : st.processLabel,
          };
        }
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
  return id === "ai_team" || id === "concierge" || id === "analytics" || id === "ai_studio" || id === "plaza";
}
