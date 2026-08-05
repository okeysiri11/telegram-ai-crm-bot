/**
 * Developer Window Inspector — Sprint 28.4.
 */

import { Badge, Button, Card } from "@/ui";
import { useDesktopStore } from "./desktopStore";
import { DESKTOP_SHORTCUTS } from "./shortcutCatalog";
import { DESKTOP_WM_VERSION } from "./types";
import { WORKSPACE_TEMPLATES } from "./workspaceProfiles";

export function WindowInspector() {
  const open = useDesktopStore((s) => s.inspectorOpen);
  const setOpen = useDesktopStore((s) => s.setInspectorOpen);
  const windows = useDesktopStore((s) => s.windows);
  const focusedId = useDesktopStore((s) => s.focusedId);
  const dock = useDesktopStore((s) => s.dock);
  const profiles = useDesktopStore((s) => s.workspaceProfiles);
  const activeProfile = useDesktopStore((s) => s.activeWorkspaceProfileId);
  const saveProfile = useDesktopStore((s) => s.saveWorkspaceProfile);
  const restoreProfile = useDesktopStore((s) => s.restoreWorkspaceProfile);
  const applyTemplate = useDesktopStore((s) => s.applyWorkspaceTemplate);
  const zCounter = useDesktopStore((s) => s.zCounter);
  const closedStack = useDesktopStore((s) => s.closedStack);

  if (!open) return null;

  const mem =
    typeof performance !== "undefined" && "memory" in performance
      ? Math.round(((performance as Performance & { memory?: { usedJSHeapSize: number } }).memory?.usedJSHeapSize || 0) / 1048576)
      : null;

  return (
    <aside className="edt-inspector ews-glass" aria-label="Window Inspector">
      <div className="row" style={{ justifyContent: "space-between", gap: 8, marginBottom: 8 }}>
        <strong>Window Inspector · {DESKTOP_WM_VERSION}</strong>
        <Button size="sm" variant="ghost" onClick={() => setOpen(false)}>
          Close
        </Button>
      </div>
      <Card title="Session">
        <p className="eds-type-small">Open windows: {windows.length}</p>
        <p className="eds-type-small">Focused: {focusedId || "—"}</p>
        <p className="eds-type-small">zCounter: {zCounter}</p>
        <p className="eds-type-small">Closed stack: {closedStack.length}</p>
        <p className="eds-type-small">Heap: {mem != null ? `${mem} MB` : "n/a"}</p>
      </Card>
      <Card title="Window tree">
        <ul className="stack-sm">
          {windows
            .slice()
            .sort((a, b) => b.zIndex - a.zIndex)
            .map((w) => (
              <li key={w.id} className="eds-type-small">
                <Badge tone={w.id === focusedId ? "info" : "default"}>{w.mode || "floating"}</Badge>{" "}
                {w.title} · z{w.zIndex} · tabs {w.tabs?.length || 1}
                {w.minimized ? " · min" : ""}
              </li>
            ))}
        </ul>
      </Card>
      <Card title="Dock hierarchy">
        <ul className="stack-sm">
          {dock.map((d) => (
            <li key={d.appId} className="eds-type-small">
              {d.appId} {d.pinned ? "(pinned)" : "(running)"}
            </li>
          ))}
        </ul>
      </Card>
      <Card title="Workspace">
        <div className="row" style={{ gap: 6, flexWrap: "wrap", marginBottom: 8 }}>
          <Button size="sm" variant="secondary" onClick={() => saveProfile(`Saved ${new Date().toLocaleTimeString()}`)}>
            Save workspace
          </Button>
          {WORKSPACE_TEMPLATES.map((t) => (
            <Button key={t.id} size="sm" variant="ghost" onClick={() => applyTemplate(t.id)}>
              {t.name}
            </Button>
          ))}
        </div>
        <ul className="stack-sm">
          {profiles.map((p) => (
            <li key={p.id} className="row" style={{ justifyContent: "space-between", gap: 8 }}>
              <span className="eds-type-small">
                {p.id === activeProfile ? "● " : ""}
                {p.name} · {p.windows.length} wins
              </span>
              <Button size="sm" variant="ghost" onClick={() => restoreProfile(p.id)}>
                Restore
              </Button>
            </li>
          ))}
        </ul>
      </Card>
      <Card title="Shortcuts">
        <ul className="stack-sm">
          {DESKTOP_SHORTCUTS.map((s) => (
            <li key={s.id} className="eds-type-helper">
              <kbd>{s.keys}</kbd> — {s.label}
            </li>
          ))}
        </ul>
      </Card>
    </aside>
  );
}
