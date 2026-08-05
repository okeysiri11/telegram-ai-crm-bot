import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/ui";
import { useDesktopStore } from "./desktopStore";
import { WALLPAPERS, DESKTOP_LAYOUTS } from "./desktopCatalog";
import type { DesktopLayoutId, WallpaperId } from "./types";
import { DesktopIcons } from "./DesktopIcons";
import { WindowFrame } from "./WindowFrame";
import { EnterpriseDock } from "./EnterpriseDock";
import { DesktopLauncher } from "./DesktopLauncher";
import { WindowInspector } from "./WindowInspector";
import { useDesktopKeyboard } from "./useDesktopKeyboard";
import { useEnterpriseStatus } from "@/command-center-runtime/useEnterpriseStatus";
import {
  useIntegrationRuntimeHealth,
  useSharedContext,
} from "@/integration-hub";
import { EnterpriseRuntimeMonitorCompact } from "@/enterprise-runtime/EnterpriseRuntimeMonitor";
import { runtimeEngine } from "@/enterprise-runtime/runtimeEngine";
import { useWorkspaceManager } from "@/workspace-engine/workspaceManagerStore";
import { useLiveDashboardStore } from "@/live-dashboard/liveDashboardStore";
import { webConfig } from "@/config/webConfig";
import { commandRuntime } from "@/runtime/commandRuntime";
import "./enterprise-desktop.css";

function DesktopMenubar() {
  const wallpaperId = useDesktopStore((s) => s.wallpaperId);
  const setWallpaper = useDesktopStore((s) => s.setWallpaper);
  const layoutId = useDesktopStore((s) => s.layoutId);
  const setLayout = useDesktopStore((s) => s.setLayout);
  const setLauncherOpen = useDesktopStore((s) => s.setLauncherOpen);
  const setInspectorOpen = useDesktopStore((s) => s.setInspectorOpen);
  const inspectorOpen = useDesktopStore((s) => s.inspectorOpen);
  const saveWorkspaceProfile = useDesktopStore((s) => s.saveWorkspaceProfile);
  const status = useEnterpriseStatus();
  const ctx = useSharedContext();
  const { items } = useIntegrationRuntimeHealth();
  const ai = items.find((i) => i.id === "ai");
  const runtime = items.find((i) => i.id === "runtime");
  const providers = items.find((i) => i.id === "providers");
  const memory = items.find((i) => i.id === "memory");

  useEffect(() => {
    runtimeEngine.publishStream("desktop", { surface: "desktop" });
    commandRuntime.setSurface("desktop");
    commandRuntime.startup();
  }, []);

  return (
    <header className="edt-menubar ews-glass" role="banner">
      <div className="edt-menubar-left">
        <span className="edt-brand">ADOS Desktop</span>
        <Button size="sm" variant="ghost" onClick={() => setLauncherOpen(true)}>
          Launcher
        </Button>
        <Button size="sm" variant="ghost" onClick={() => saveWorkspaceProfile(`Session ${new Date().toLocaleTimeString()}`)}>
          Save WS
        </Button>
        <Button size="sm" variant="ghost" onClick={() => setInspectorOpen(!inspectorOpen)}>
          Inspector
        </Button>
        <button
          type="button"
          className="eds-type-helper text-[var(--eds-primary)]"
          onClick={() => {
            commandRuntime.setSurface("desktop");
            commandRuntime.executeSync("desktop_open_city");
          }}
        >
          Enterprise City
        </button>
        <button
          type="button"
          className="eds-type-helper text-[var(--eds-primary)]"
          onClick={() => {
            commandRuntime.setSurface("desktop");
            commandRuntime.executeSync("desktop_open_production");
          }}
        >
          Production
        </button>
        <button
          type="button"
          className="eds-type-helper text-[var(--eds-primary)]"
          onClick={() => {
            commandRuntime.setSurface("desktop");
            commandRuntime.executeSync("desktop_open_crm");
          }}
        >
          CRM
        </button>
        <Link to="/dashboard" className="eds-type-helper text-[var(--eds-primary)]">
          Classic UI
        </Link>
      </div>
      <div className="edt-menubar-right">
        <span className="eds-type-helper" title="Shared context">
          {ctx.organization} · {ctx.project} · {ctx.profileId}
        </span>
        <label className="edt-field">
          <span className="eds-type-helper">Wallpaper</span>
          <select
            value={wallpaperId}
            onChange={(e) => setWallpaper(e.target.value as WallpaperId)}
            aria-label="Wallpaper"
          >
            {(Object.keys(WALLPAPERS) as WallpaperId[]).map((id) => (
              <option key={id} value={id}>
                {WALLPAPERS[id].label}
              </option>
            ))}
          </select>
        </label>
        <label className="edt-field">
          <span className="eds-type-helper">Layout</span>
          <select
            value={layoutId}
            onChange={(e) => setLayout(e.target.value as DesktopLayoutId)}
            aria-label="Desktop layout"
          >
            {(Object.keys(DESKTOP_LAYOUTS) as DesktopLayoutId[]).map((id) => (
              <option key={id} value={id}>
                {DESKTOP_LAYOUTS[id].label}
              </option>
            ))}
          </select>
        </label>
        <EnterpriseRuntimeMonitorCompact />
        <span className="edt-status-chip" title="Runtime">
          <span className={`ews-dot ews-dot--${runtime?.tone || "unknown"}`} aria-hidden />
          Runtime
        </span>
        <span className="edt-status-chip" title="Memory">
          <span className={`ews-dot ews-dot--${memory?.tone || "ok"}`} aria-hidden />
          Mem
        </span>
        <span className="edt-status-chip" title="AI">
          <span className={`ews-dot ews-dot--${ai?.tone || "ok"}`} aria-hidden />
          AI
        </span>
        <span className="edt-status-chip" title="Providers">
          <span className={`ews-dot ews-dot--${providers?.tone || "ok"}`} aria-hidden />
          Providers
        </span>
        <span className="edt-status-chip" title="Notifications">
          Alerts {status.unread}
        </span>
        <span className="edt-status-chip" title="Jobs">
          Jobs {status.jobs}
        </span>
        <span className="eds-type-helper">Sprint {webConfig.sprint}</span>
      </div>
    </header>
  );
}

/**
 * Sprint 27.7 — Enterprise Desktop Environment shell.
 * Canvas · wallpaper · icons · windows · dock · launcher.
 */
export function DesktopShell() {
  const hydrate = useDesktopStore((s) => s.hydrate);
  const hydrated = useDesktopStore((s) => s.hydrated);
  const wallpaperId = useDesktopStore((s) => s.wallpaperId);
  const windows = useDesktopStore((s) => s.windows);
  const snapPreview = useDesktopStore((s) => s.snapPreview);
  const setProfile = useDesktopStore((s) => s.setProfile);
  const setActiveWorkspaceId = useDesktopStore((s) => s.setActiveWorkspaceId);
  const wsId = useWorkspaceManager((s) => s.activeWorkspaceId);
  const dashProfile = useLiveDashboardStore((s) => s.profileId);

  useDesktopKeyboard();

  useEffect(() => {
    hydrate();
    document.title = "ADOS Desktop · Enterprise OS";
  }, [hydrate]);

  useEffect(() => {
    if (!hydrated) return;
    if (wsId) setActiveWorkspaceId(wsId);
    if (dashProfile) setProfile(dashProfile);
  }, [hydrated, wsId, dashProfile, setActiveWorkspaceId, setProfile]);

  if (!hydrated) {
    return <p className="eds-type-helper p-6">Loading Enterprise Desktop…</p>;
  }

  const wallpaper = WALLPAPERS[wallpaperId]?.css || WALLPAPERS.aurora.css;
  const visible = windows.filter((w) => !w.minimized);

  return (
    <div className="edt-shell" style={{ background: wallpaper }}>
      <DesktopMenubar />
      <main className="edt-canvas" aria-label="Desktop canvas">
        <DesktopIcons />
        {snapPreview ? (
          <div
            className="edt-snap-preview"
            style={{
              left: snapPreview.bounds.x,
              top: snapPreview.bounds.y,
              width: snapPreview.bounds.width,
              height: snapPreview.bounds.height,
            }}
            aria-hidden
          />
        ) : null}
        {visible.map((w) => (
          <WindowFrame key={w.id} win={w} />
        ))}
        <WindowInspector />
      </main>
      <DesktopLauncher />
      <EnterpriseDock />
    </div>
  );
}
