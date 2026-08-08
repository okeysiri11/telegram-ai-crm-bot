import { useMemo, useState } from "react";
import { Input } from "@/ui";
import { ShellIcon } from "@/shell/enterprise/ShellIcons";
import type { ShellIconId } from "@/shell/enterprise/enterpriseNav";
import { DESKTOP_APPS } from "./desktopCatalog";
import { useDesktopStore } from "./desktopStore";
import { commandRuntime, launcherRegistry } from "@/runtime/commandRuntime";

const GROUPS = [
  { id: "core", label: "Основное" },
  { id: "ai", label: "AI" },
  { id: "ops", label: "Операции" },
  { id: "tools", label: "Инструменты" },
] as const;

/** Application launcher — Ctrl/Cmd+Space. Sprint 42.9 RU. */
export function DesktopLauncher() {
  const open = useDesktopStore((s) => s.launcherOpen);
  const setLauncherOpen = useDesktopStore((s) => s.setLauncherOpen);
  const [q, setQ] = useState("");
  const [favorites, setFavorites] = useState<string[]>(() => {
    try {
      return JSON.parse(localStorage.getItem("ewp_launcher_fav_v1") || "[]") as string[];
    } catch {
      return [];
    }
  });
  const [recent, setRecent] = useState<string[]>(() => {
    try {
      return JSON.parse(localStorage.getItem("ewp_launcher_recent_v1") || "[]") as string[];
    } catch {
      return [];
    }
  });

  const filtered = useMemo(() => {
    const query = q.trim().toLowerCase();
    if (!query) return DESKTOP_APPS;
    return DESKTOP_APPS.filter((a) => `${a.label} ${a.id} ${a.group}`.toLowerCase().includes(query));
  }, [q]);

  function persistFav(next: string[]) {
    setFavorites(next);
    try {
      localStorage.setItem("ewp_launcher_fav_v1", JSON.stringify(next));
    } catch {
      /* ignore */
    }
  }

  function toggleFav(id: string) {
    persistFav(favorites.includes(id) ? favorites.filter((x) => x !== id) : [...favorites, id].slice(0, 24));
  }

  function openApp(appId: string, path: string) {
    commandRuntime.setSurface("desktop");
    const commandId = launcherRegistry.resolveCommandId(appId);
    commandRuntime.executeSync(commandId, { path, appId });
    const nextRecent = [appId, ...recent.filter((x) => x !== appId)].slice(0, 8);
    setRecent(nextRecent);
    try {
      localStorage.setItem("ewp_launcher_recent_v1", JSON.stringify(nextRecent));
    } catch {
      /* ignore */
    }
    setLauncherOpen(false);
  }

  if (!open) return null;

  const favApps = DESKTOP_APPS.filter((a) => favorites.includes(a.id));
  const recentApps = recent
    .map((id) => DESKTOP_APPS.find((a) => a.id === id))
    .filter(Boolean) as typeof DESKTOP_APPS;

  return (
    <div
      className="edt-launcher-backdrop"
      role="presentation"
      onMouseDown={() => setLauncherOpen(false)}
    >
      <div
        className="edt-launcher ews-glass edm-overlay-panel"
        role="dialog"
        aria-label="Запуск приложений"
        data-testid="desktop-launcher"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <Input
          autoFocus
          placeholder="Поиск приложений…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Поиск приложений"
        />

        {!q.trim() && favApps.length ? (
          <div className="edt-launcher-group mt-3">
            <p className="eds-type-section">Избранное</p>
            <ul>
              {favApps.map((a) => (
                <li key={`fav-${a.id}`}>
                  <button type="button" className="edt-launcher-app" onClick={() => openApp(a.id, a.path)}>
                    <ShellIcon id={a.icon as ShellIconId} className="edt-launcher-icon" />
                    <span>{a.label}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {!q.trim() && recentApps.length ? (
          <div className="edt-launcher-group mt-2">
            <p className="eds-type-section">Недавние</p>
            <ul>
              {recentApps.map((a) => (
                <li key={`recent-${a.id}`}>
                  <button type="button" className="edt-launcher-app" onClick={() => openApp(a.id, a.path)}>
                    <ShellIcon id={a.icon as ShellIconId} className="edt-launcher-icon" />
                    <span>{a.label}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="edt-launcher-grid">
          {GROUPS.map((g) => {
            const apps = filtered.filter((a) => a.group === g.id);
            if (!apps.length) return null;
            return (
              <div key={g.id} className="edt-launcher-group">
                <p className="eds-type-section">{g.label}</p>
                <ul>
                  {apps.map((a) => (
                    <li key={a.id} className="flex items-center gap-1">
                      <button
                        type="button"
                        className="edt-launcher-app flex-1"
                        onClick={() => openApp(a.id, a.path)}
                      >
                        <ShellIcon id={a.icon as ShellIconId} className="edt-launcher-icon" />
                        <span>{a.label}</span>
                      </button>
                      <button
                        type="button"
                        className="eds-type-caption px-1"
                        title={favorites.includes(a.id) ? "Открепить" : "Закрепить"}
                        aria-label={favorites.includes(a.id) ? "Открепить" : "Закрепить"}
                        onClick={() => toggleFav(a.id)}
                      >
                        {favorites.includes(a.id) ? "★" : "☆"}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
        <p className="eds-type-helper mt-2">Поиск · категории · избранное · недавние</p>
      </div>
    </div>
  );
}
