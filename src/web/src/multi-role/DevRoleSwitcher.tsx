/**
 * Sprint 42.1 / 42.6 — Developer-only tools (role switcher + optional tab strip).
 */

import { useNavigate } from "react-router-dom";
import { Select, Switch } from "@/ui";
import { useViewModeStore } from "@/ux-revolution";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { switchRoleSession } from "./roleSessionVault";
import { homeRouteForRole, mapToRoleHomeId } from "@/navigation/roleHome";
import { useI18n } from "@/i18n";
import type { ViewModeId } from "@/ux-revolution/viewModeCatalog";
import { useWorkspaceTabChromeStore } from "@/workspace-engine/workspaceTabChromeStore";

const DEV_ROLES: Array<{ id: string; label: string; viewMode: ViewModeId }> = [
  { id: "owner", label: "Owner", viewMode: "platform_owner" },
  { id: "client", label: "Client", viewMode: "client" },
  { id: "manager", label: "Manager", viewMode: "manager" },
  { id: "sales", label: "Sales", viewMode: "manager" },
  { id: "support", label: "Support", viewMode: "manager" },
];

export function DevRoleSwitcher() {
  const t = useI18n((s) => s.t);
  const viewMode = useViewModeStore((s) => s.viewMode);
  const setViewMode = useViewModeStore((s) => s.setViewMode);
  const activeRoleId = useRoleSwitcher((s) => s.activeRoleId);
  const setRole = useRoleSwitcher((s) => s.setRole);
  const navigate = useNavigate();
  const tabChromeEnabled = useWorkspaceTabChromeStore((s) => s.enabled);
  const setTabChromeEnabled = useWorkspaceTabChromeStore((s) => s.setEnabled);

  const enabled =
    viewMode === "developer" ||
    (import.meta.env.DEV && import.meta.env.VITE_DEV_ROLE_SWITCHER === "true");

  if (!enabled) return null;

  function onSwitch(nextId: string) {
    const def = DEV_ROLES.find((r) => r.id === nextId);
    if (!def) return;
    switchRoleSession(activeRoleId, nextId);
    setRole(nextId);
    setViewMode(def.viewMode);
    const home = homeRouteForRole(mapToRoleHomeId(nextId === "sales" ? "sales" : nextId));
    navigate(home);
  }

  return (
    <span
      className="hidden items-center gap-2 eds-type-caption lg:inline-flex"
      data-testid="dev-role-switcher"
    >
      <label className="inline-flex items-center gap-1">
        <span className="text-[var(--eds-text-muted)]">{t("devRole.label")}</span>
        <Select
          className="eds-focus-ring max-w-[8rem]"
          value={DEV_ROLES.some((r) => r.id === activeRoleId) ? activeRoleId : "owner"}
          onChange={(e) => onSwitch(e.target.value)}
          aria-label={t("devRole.label")}
        >
          {DEV_ROLES.map((r) => (
            <option key={r.id} value={r.id}>
              {r.label}
            </option>
          ))}
        </Select>
      </label>
      {viewMode === "developer" ? (
        <span data-testid="dev-workspace-tabs-header-toggle">
          <Switch
            checked={tabChromeEnabled}
            onChange={(v) => setTabChromeEnabled(v)}
            label={t("devTabs.short")}
          />
        </span>
      ) : null}
    </span>
  );
}
