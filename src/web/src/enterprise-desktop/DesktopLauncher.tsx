import { useMemo, useState } from "react";
import { Input } from "@/ui";
import { ShellIcon } from "@/shell/enterprise/ShellIcons";
import type { ShellIconId } from "@/shell/enterprise/enterpriseNav";
import { DESKTOP_APPS } from "./desktopCatalog";
import { useDesktopStore } from "./desktopStore";
import { commandRuntime, launcherRegistry } from "@/runtime/commandRuntime";

const GROUPS = [
  { id: "core", label: "Core" },
  { id: "ai", label: "AI" },
  { id: "ops", label: "Operations" },
  { id: "tools", label: "Tools" },
] as const;

/** Application launcher — Ctrl/Cmd+Space. Executes via Command Runtime registry IDs. */
export function DesktopLauncher() {
  const open = useDesktopStore((s) => s.launcherOpen);
  const setLauncherOpen = useDesktopStore((s) => s.setLauncherOpen);
  const [q, setQ] = useState("");

  const filtered = useMemo(() => {
    const query = q.trim().toLowerCase();
    if (!query) return DESKTOP_APPS;
    return DESKTOP_APPS.filter((a) => `${a.label} ${a.id} ${a.group}`.toLowerCase().includes(query));
  }, [q]);

  if (!open) return null;

  return (
    <div
      className="edt-launcher-backdrop"
      role="presentation"
      onMouseDown={() => setLauncherOpen(false)}
    >
      <div
        className="edt-launcher ews-glass edm-overlay-panel"
        role="dialog"
        aria-label="Application launcher"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <Input
          autoFocus
          placeholder="Search applications…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Search apps"
        />
        <div className="edt-launcher-grid">
          {GROUPS.map((g) => {
            const apps = filtered.filter((a) => a.group === g.id);
            if (!apps.length) return null;
            return (
              <div key={g.id} className="edt-launcher-group">
                <p className="eds-type-section">{g.label}</p>
                <ul>
                  {apps.map((a) => (
                    <li key={a.id}>
                      <button
                        type="button"
                        className="edt-launcher-app"
                        onClick={() => {
                          commandRuntime.setSurface("desktop");
                          const commandId = launcherRegistry.resolveCommandId(a.id);
                          commandRuntime.executeSync(commandId, { path: a.path, appId: a.id });
                          setLauncherOpen(false);
                        }}
                      >
                        <ShellIcon id={a.icon as ShellIconId} className="edt-launcher-icon" />
                        <span>{a.label}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
        <p className="eds-type-helper mt-2">
          Registry IDs only · Command Runtime {commandRuntime.version}
        </p>
      </div>
    </div>
  );
}
