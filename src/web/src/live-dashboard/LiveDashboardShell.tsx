import { useEffect, useState } from "react";
import { Button, Input } from "@/ui";
import { useLiveDashboardStore } from "./liveDashboardStore";
import { DASHBOARD_PROFILES } from "./liveDashboardCatalog";
import type { DashboardProfileId } from "./types";
import { LiveDashboardWidget } from "./LiveDashboardWidgets";
import { useDashboardEventBus } from "./dashboardEventBus";
import { LiveDashboardDataProvider, useLiveDashboardData } from "./LiveDashboardDataContext";
import "./liveDashboard.css";

function LiveDashboardInner() {
  const profileId = useLiveDashboardStore((s) => s.profileId);
  const setProfile = useLiveDashboardStore((s) => s.setProfile);
  const layouts = useLiveDashboardStore((s) => s.layouts);
  const activeLayoutId = useLiveDashboardStore((s) => s.activeLayoutId);
  const setActiveLayout = useLiveDashboardStore((s) => s.setActiveLayout);
  const saveCurrentAs = useLiveDashboardStore((s) => s.saveCurrentAs);
  const restoreProfileLayout = useLiveDashboardStore((s) => s.restoreProfileLayout);
  const fullscreenId = useLiveDashboardStore((s) => s.fullscreenId);
  const setFullscreen = useLiveDashboardStore((s) => s.setFullscreen);
  const getActiveWidgets = useLiveDashboardStore((s) => s.getActiveWidgets);
  const tick = useLiveDashboardStore((s) => s.tick);
  const [layoutName, setLayoutName] = useState("");
  const { metrics } = useLiveDashboardData();

  void tick;
  const widgets = getActiveWidgets();
  const fsWidget = fullscreenId ? widgets.find((w) => w.id === fullscreenId) : null;

  return (
    <section className="eld-shell" aria-label="Enterprise Live Dashboard">
      <div className="eld-toolbar ews-glass">
        <div>
          <p className="eds-type-section">Live Dashboard</p>
          <p className="eds-type-helper">
            Auto-updating · CPU {metrics.cpuPct}% · Mem {metrics.memoryPct}% · Agents {metrics.activeAgents} · Jobs{" "}
            {metrics.backgroundJobs}
          </p>
        </div>
        <div className="eld-toolbar-controls">
          <label className="eld-field">
            <span className="eds-type-helper">Profile</span>
            <select
              value={profileId}
              onChange={(e) => setProfile(e.target.value as DashboardProfileId)}
              aria-label="Dashboard profile"
            >
              {(Object.keys(DASHBOARD_PROFILES) as DashboardProfileId[]).map((id) => (
                <option key={id} value={id}>
                  {DASHBOARD_PROFILES[id].label}
                </option>
              ))}
            </select>
          </label>
          <label className="eld-field">
            <span className="eds-type-helper">Layout</span>
            <select
              value={activeLayoutId}
              onChange={(e) => setActiveLayout(e.target.value)}
              aria-label="Dashboard layout"
            >
              {layouts.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name}
                </option>
              ))}
            </select>
          </label>
          <Input
            className="eld-save-input"
            placeholder="Save layout as…"
            value={layoutName}
            onChange={(e) => setLayoutName(e.target.value)}
            aria-label="New layout name"
          />
          <Button
            size="sm"
            variant="secondary"
            onClick={() => {
              saveCurrentAs(layoutName);
              setLayoutName("");
            }}
          >
            Save layout
          </Button>
          <Button size="sm" variant="ghost" onClick={() => restoreProfileLayout()}>
            Restore profile
          </Button>
        </div>
      </div>

      <p className="eds-type-helper mb-2">{DASHBOARD_PROFILES[profileId].description}</p>

      {fsWidget ? (
        <div className="eld-fullscreen-host">
          <LiveDashboardWidget placement={fsWidget} />
          <Button size="sm" variant="secondary" className="eld-fs-close" onClick={() => setFullscreen(null)}>
            Close fullscreen
          </Button>
        </div>
      ) : (
        <div className="eld-grid" role="list">
          {widgets.map((w) => (
            <div key={w.id} role="listitem" className="eld-grid-item" style={{ gridColumn: `span ${w.colSpan}` }}>
              <LiveDashboardWidget placement={w} />
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

/**
 * Sprint 27.6 — Live Enterprise Dashboard shell.
 * Profiles · move/resize · save/restore · auto-updating widgets.
 */
export function LiveDashboardShell() {
  const hydrate = useLiveDashboardStore((s) => s.hydrate);
  const hydrated = useLiveDashboardStore((s) => s.hydrated);

  useDashboardEventBus();

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  if (!hydrated) {
    return <p className="eds-type-helper">Loading live dashboard…</p>;
  }

  return (
    <LiveDashboardDataProvider>
      <LiveDashboardInner />
    </LiveDashboardDataProvider>
  );
}
