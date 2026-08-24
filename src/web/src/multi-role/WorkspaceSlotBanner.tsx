/**
 * Sprint 42.1 — workspace slot banner + Open Demo Workspace CTA.
 */

import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/ui";
import { getWorkspaceSlot, workspaceSlotLabel } from "./workspaceSlot";
import { openClientDemoWorkspace } from "./applyDemoSession";
import { useAuthStore } from "@/auth/authStore";
import { useI18n } from "@/i18n";
import { useViewModeStore } from "@/ux-revolution";

export function WorkspaceSlotBanner() {
  const t = useI18n((s) => s.t);
  const slot = getWorkspaceSlot();
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const viewMode = useViewModeStore((s) => s.viewMode);

  async function openDemo() {
    const creds = openClientDemoWorkspace();
    try {
      await login(creds.email, creds.password, creds.tenantId);
    } catch {
      /* demo seed still applied for already-logged-in users */
    }
    navigate("/dashboard");
  }

  return (
    <div
      className="mb-2 flex flex-wrap items-center justify-between gap-2 rounded-md border border-[var(--ew-border)] bg-[var(--eds-surface)] px-3 py-1.5"
      data-testid="workspace-slot-banner"
    >
      <p className="eds-type-caption">
        <span className="text-[var(--eds-text-muted)]">{t("workspace.slot")}: </span>
        <strong>{workspaceSlotLabel(slot)}</strong>
        {typeof window !== "undefined" && window.location.port && !/trycloudflare|cloudflare/.test(window.location.hostname) ? (
          <span className="text-[var(--eds-text-muted)]"> · :{window.location.port}</span>
        ) : null}
      </p>
      <div className="flex flex-wrap gap-2">
        {(viewMode === "client" || viewMode === "developer" || import.meta.env.DEV) && (
          <Button size="sm" className="ews-primary-cta" onClick={() => void openDemo()} data-testid="open-demo-workspace">
            {t("workspace.openDemo")}
          </Button>
        )}
        <Link to="/settings?tab=interface" className="eds-type-caption text-[var(--eds-accent)]">
          {t("nav.settings")}
        </Link>
      </div>
    </div>
  );
}
