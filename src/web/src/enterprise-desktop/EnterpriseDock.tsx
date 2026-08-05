import { useMemo, useState } from "react";
import { ShellIcon } from "@/shell/enterprise/ShellIcons";
import type { ShellIconId } from "@/shell/enterprise/enterpriseNav";
import { useDesktopStore } from "./desktopStore";
import { appById, DESKTOP_APPS } from "./desktopCatalog";
import { useNotificationStore } from "@/notifications/notificationStore";
import { useRuntimeHealth } from "@/shell/enterprise/useRuntimeHealth";

function badgeFor(appId: string, unread: number, jobs: number, aiWarn: boolean): number | undefined {
  const app = appById(appId);
  if (!app?.badgeKey) return undefined;
  if (app.badgeKey === "notifications") return unread || undefined;
  if (app.badgeKey === "jobs") return jobs || undefined;
  if (app.badgeKey === "ai") return aiWarn ? 1 : undefined;
  return undefined;
}

/** macOS-style Enterprise Dock — pinned, running, badges, hover. */
export function EnterpriseDock() {
  const dock = useDesktopStore((s) => s.dock);
  const windows = useDesktopStore((s) => s.windows);
  const recentAppIds = useDesktopStore((s) => s.recentAppIds);
  const openApp = useDesktopStore((s) => s.openApp);
  const setLauncherOpen = useDesktopStore((s) => s.setLauncherOpen);
  const minimizeWindow = useDesktopStore((s) => s.minimizeWindow);
  const restoreWindow = useDesktopStore((s) => s.restoreWindow);
  const focusWindow = useDesktopStore((s) => s.focusWindow);
  const items = useNotificationStore((s) => s.items);
  const { items: health } = useRuntimeHealth(45_000);
  const [hover, setHover] = useState<string | null>(null);

  const unread = useMemo(() => items.filter((i) => !i.read).length, [items]);
  const jobs = useMemo(
    () => items.filter((i) => i.kind === "job" || i.kind === "workflow" || i.kind === "task").length,
    [items],
  );
  const aiWarn = health.some((h) => (h.id === "ai" || h.id === "providers") && (h.tone === "warn" || h.tone === "err"));

  const dockApps = dock
    .map((d) => appById(d.appId))
    .filter(Boolean)
    .concat(
      recentAppIds
        .filter((id) => !dock.some((d) => d.appId === id))
        .slice(0, 3)
        .map((id) => appById(id))
        .filter(Boolean),
    );

  function onDockClick(appId: string) {
    const wins = windows.filter((w) => w.appId === appId);
    if (!wins.length) {
      openApp(appId);
      return;
    }
    const focused = wins.find((w) => !w.minimized);
    if (focused) {
      minimizeWindow(focused.id);
      return;
    }
    const min = wins.find((w) => w.minimized);
    if (min) restoreWindow(min.id);
    else focusWindow(wins[0]!.id);
  }

  return (
    <footer className="edt-dock" role="toolbar" aria-label="Enterprise Dock">
      <button
        type="button"
        className="edt-dock-item edt-dock-launcher"
        aria-label="Open launcher"
        onClick={() => setLauncherOpen(true)}
      >
        <span className="edt-dock-glyph">⌘</span>
      </button>
      <div className="edt-dock-sep" aria-hidden />
      {dockApps.map((app) => {
        if (!app) return null;
        const running = windows.some((w) => w.appId === app.id);
        const badge = badgeFor(app.id, unread, jobs, aiWarn);
        const scale = hover === app.id ? 1.18 : 1;
        return (
          <button
            key={app.id}
            type="button"
            className={`edt-dock-item${running ? " is-running" : ""}`}
            title={app.label}
            aria-label={app.label}
            style={{ transform: `scale(${scale})` }}
            onMouseEnter={() => setHover(app.id)}
            onMouseLeave={() => setHover(null)}
            onClick={() => onDockClick(app.id)}
          >
            <ShellIcon id={app.icon as ShellIconId} className="edt-dock-icon" />
            {badge ? <span className="edt-dock-badge">{badge > 9 ? "9+" : badge}</span> : null}
            {running ? <span className="edt-dock-dot" aria-hidden /> : null}
          </button>
        );
      })}
      <div className="edt-dock-sep" aria-hidden />
      <span className="edt-dock-meta eds-type-helper">
        {DESKTOP_APPS.length} apps · {windows.filter((w) => !w.minimized).length} open
      </span>
    </footer>
  );
}
