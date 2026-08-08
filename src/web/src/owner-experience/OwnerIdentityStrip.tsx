/**
 * Sprint 42.9 — Owner identity + «Работаю как» in the header.
 */

import { useNavigate } from "react-router-dom";
import { Select } from "@/ui";
import { useAuthStore } from "@/auth/authStore";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { useViewModeStore } from "@/ux-revolution";
import { useVerticalWorkspaceStore } from "@/vertical-workspace/verticalWorkspaceStore";
import { VERTICAL_BY_ID } from "@/vertical-workspace/catalog";
import { homeRouteForRole, mapToRoleHomeId } from "@/navigation/roleHome";
import {
  WORK_AS_OPTIONS,
  workAsFromViewMode,
  workAsLabel,
  type WorkAsId,
} from "./workAsCatalog";

export function OwnerIdentityStrip() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const viewMode = useViewModeStore((s) => s.viewMode);
  const setViewMode = useViewModeStore((s) => s.setViewMode);
  const setRole = useRoleSwitcher((s) => s.setRole);
  const orgLabel = useOrgSelector((s) => s.label());
  const verticalId = useVerticalWorkspaceStore((s) => s.verticalId);
  const setVerticalId = useVerticalWorkspaceStore((s) => s.setVerticalId);
  const workspaceLabel = VERTICAL_BY_ID[verticalId]?.label || verticalId;
  const workAs = workAsFromViewMode(viewMode);

  function onWorkAs(next: WorkAsId) {
    const opt = WORK_AS_OPTIONS.find((o) => o.id === next);
    if (!opt) return;
    setViewMode(opt.viewMode);
    setRole(opt.roleSwitcherId);
    const home = homeRouteForRole(mapToRoleHomeId(opt.roleSwitcherId));
    navigate(home);
  }

  function onWorkspace(next: string) {
    setVerticalId(next);
    navigate(`/vertical/${next}`);
  }

  return (
    <div className="oe-identity" data-testid="owner-identity-strip">
      <div className="oe-identity-user">
        <span className="oe-identity-avatar" aria-hidden>
          👤
        </span>
        <div className="min-w-0">
          <p className="eds-type-caption text-[var(--eds-text-muted)] leading-none">Пользователь</p>
          <p className="eds-type-small truncate font-semibold" title={user?.name || "Гость"}>
            {user?.name || "Гость"}
          </p>
        </div>
      </div>

      <label className="oe-identity-field">
        <span className="eds-type-caption text-[var(--eds-text-muted)]">Работаю как</span>
        <Select
          className="eds-focus-ring max-w-[11rem]"
          value={workAs}
          onChange={(e) => onWorkAs(e.target.value as WorkAsId)}
          aria-label="Работаю как"
          data-testid="work-as-select"
        >
          {WORK_AS_OPTIONS.map((o) => (
            <option key={o.id} value={o.id}>
              {o.label}
            </option>
          ))}
        </Select>
      </label>

      <div className="oe-identity-field hidden lg:block">
        <p className="eds-type-caption text-[var(--eds-text-muted)] leading-none">Роль</p>
        <p className="eds-type-small font-medium">{workAsLabel(workAs)}</p>
      </div>

      <div className="oe-identity-field">
        <p className="eds-type-caption text-[var(--eds-text-muted)] leading-none">Организация</p>
        <p className="eds-type-small max-w-[8rem] truncate font-semibold" title={orgLabel}>
          {orgLabel}
        </p>
      </div>

      <label className="oe-identity-field">
        <span className="eds-type-caption text-[var(--eds-text-muted)]">Рабочее пространство</span>
        <Select
          className="eds-focus-ring max-w-[10rem]"
          value={verticalId}
          onChange={(e) => onWorkspace(e.target.value)}
          aria-label="Рабочее пространство"
          data-testid="identity-workspace-select"
        >
          {Object.values(VERTICAL_BY_ID).map((v) => (
            <option key={v.id} value={v.id}>
              {v.label}
            </option>
          ))}
        </Select>
        <span className="sr-only">{workspaceLabel}</span>
      </label>
    </div>
  );
}
