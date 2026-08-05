/**
 * Governance chrome strip — Sprint 1.1.1 (split from page for route-level code split).
 */

import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Badge } from "@/ui";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { useAuthStore } from "@/auth/authStore";
import { telemetry } from "@/integrations/telemetry";
import { deriveGovernance } from "./deriveGovernance";

export function GovernanceStrip() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const first = loadFirstEntry();
  const user = useAuthStore((s) => s.user);
  const gov = useMemo(
    () =>
      deriveGovernance(snapshot, {
        notifications,
        roleId: user?.roleId || first.roleId,
        permissions: user?.permissions,
      }),
    [snapshot, notifications, user?.roleId, user?.permissions, first.roleId],
  );
  const pending = gov.approvalQueue.filter((a) => a.queue === "pending" || a.queue === "critical").length;
  return (
    <div className="gov-strip" aria-label="Governance">
      <span className="gov-strip-label">Governance</span>
      <Badge tone="success">{gov.compliance.compliancePct}%</Badge>
      {pending ? <Badge tone="danger">{pending} queue</Badge> : <Badge>clear</Badge>}
      <Link
        to="/platform-builder/governance"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("gov_open")}
      >
        Policies →
      </Link>
    </div>
  );
}
