/**
 * Sprint 42.8 — переключатель рабочего пространства (рядом с организацией).
 */

import { useNavigate } from "react-router-dom";
import { Select } from "@/ui";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { VERTICAL_WORKSPACES } from "./catalog";
import { useVerticalWorkspaceStore } from "./verticalWorkspaceStore";

export function WorkspaceSwitcher() {
  const navigate = useNavigate();
  const orgLabel = useOrgSelector((s) => s.label());
  const verticalId = useVerticalWorkspaceStore((s) => s.verticalId);
  const setVerticalId = useVerticalWorkspaceStore((s) => s.setVerticalId);

  function onChange(next: string) {
    setVerticalId(next);
    const v = VERTICAL_WORKSPACES.find((x) => x.id === next);
    navigate(v?.route || `/vertical/${next}`);
  }

  return (
    <div
      className="uvw-switcher hidden items-center gap-2 md:flex"
      data-testid="workspace-switcher"
    >
      <div className="min-w-0">
        <p className="eds-type-caption text-[var(--eds-text-muted)] leading-none">Организация</p>
        <p className="eds-type-small max-w-[9rem] truncate font-semibold" title={orgLabel}>
          {orgLabel}
        </p>
      </div>
      <label className="inline-flex min-w-[10rem] flex-col gap-0.5">
        <span className="eds-type-caption text-[var(--eds-text-muted)]">Рабочее пространство</span>
        <Select
          className="eds-focus-ring max-w-[12rem]"
          value={verticalId}
          onChange={(e) => onChange(e.target.value)}
          aria-label="Рабочее пространство"
          data-testid="workspace-switcher-select"
        >
          {VERTICAL_WORKSPACES.map((v) => (
            <option key={v.id} value={v.id}>
              {v.label}
            </option>
          ))}
        </Select>
      </label>
    </div>
  );
}
