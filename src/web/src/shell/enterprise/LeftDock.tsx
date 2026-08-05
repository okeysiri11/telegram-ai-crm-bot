import { Link } from "react-router-dom";
import { ShellIcon } from "./ShellIcons";
import { DockPanel } from "./DockPanel";
import { useShellLayoutStore } from "./shellLayoutStore";
import { useWorkspaceNavigation } from "@/workspace-engine/useWorkspaceTabs";
import { shellModuleRegistry } from "./shellModuleRegistry";
import { buildActivityTimeline } from "./activityTimeline";
import type { ShellIconId } from "./enterpriseNav";

/**
 * Sprint 27.4 / 28.5 — left dock: module shortcuts + recent activity.
 */
export function LeftDock() {
  const open = useShellLayoutStore((s) => s.docks.left.open);
  const { open: openTab } = useWorkspaceNavigation();
  const recent = buildActivityTimeline(5);
  const shortcuts = shellModuleRegistry.toNavItems().slice(0, 10);

  if (!open) return null;

  return (
    <DockPanel side="left" title="Workspace Dock" subtitle="Modules · recent" className="ews-left-dock">
      <nav className="ews-left-dock-nav" aria-label="Dock module shortcuts">
        {shortcuts.map((item) => (
          <button
            key={item.id}
            type="button"
            className="ews-left-dock-link"
            onClick={() => openTab(item.route)}
          >
            <ShellIcon id={item.icon as ShellIconId} className="ews-left-dock-icon" />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="ews-left-dock-recent">
        <p className="eds-type-helper mb-1">Recent</p>
        <ul className="space-y-1">
          {recent.map((e) => (
            <li key={e.id} className="eds-type-small truncate" title={e.detail}>
              {e.title}
            </li>
          ))}
          {!recent.length ? <li className="eds-type-helper">Open a module to populate.</li> : null}
        </ul>
        <Link to="/search" className="mt-2 inline-block eds-type-helper text-[var(--eds-primary)]">
          Search workspace →
        </Link>
      </div>
    </DockPanel>
  );
}
