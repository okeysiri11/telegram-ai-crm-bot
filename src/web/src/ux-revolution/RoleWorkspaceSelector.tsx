/**
 * Sprint 33.1 — Role Workspace selector (Who are you? / switch workspace).
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Select } from "@/ui";
import {
  ENTERPRISE_UX_ROLES,
  loadRoleWorkspaceId,
  saveRoleWorkspaceId,
  roleWorkspaceById,
} from "./roleWorkspaceCatalog";
import { ensureProMode } from "./ensureProMode";

export function RoleWorkspaceSelector({
  className,
  navigateOnChange = true,
}: {
  className?: string;
  navigateOnChange?: boolean;
} = {}) {
  const navigate = useNavigate();
  const [roleId, setRoleId] = useState(() => loadRoleWorkspaceId() || "ceo");

  useEffect(() => {
    saveRoleWorkspaceId(roleId);
  }, [roleId]);

  function onChange(next: string) {
    setRoleId(next);
    saveRoleWorkspaceId(next);
    const ws = roleWorkspaceById(next);
    if (!ws) return;
    if (next === "developer" || next === "production" || next === "administrator") {
      ensureProMode("Switched to Pro Mode");
    }
    if (navigateOnChange) {
      navigate(ws.homeRoute);
    }
  }

  return (
    <label className={className ?? "hidden items-center gap-1 eds-type-caption xl:inline-flex"}>
      <span className="text-[var(--eds-text-muted)]">Роль</span>
      <Select
        className="eds-focus-ring max-w-[10rem]"
        aria-label="Рабочее пространство по роли"
        value={roleId}
        onChange={(e) => onChange(e.target.value)}
      >
        {ENTERPRISE_UX_ROLES.map((r) => (
          <option key={r.id} value={r.id}>
            {r.label}
          </option>
        ))}
      </Select>
    </label>
  );
}
