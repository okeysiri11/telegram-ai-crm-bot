/** Autonomy strip — Sprint 1.1.1. */

import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Badge } from "@/ui";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { telemetry } from "@/integrations/telemetry";
import { deriveAutonomy } from "./deriveAutonomy";

export function AutonomyStrip() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const first = loadFirstEntry();
  const bundle = useMemo(
    () => deriveAutonomy(snapshot, { roleId: first.roleId, notifications }),
    [snapshot, first.roleId, notifications],
  );
  return (
    <div className="auto-strip" aria-label="Autonomy">
      <span className="auto-strip-label">Autonomy</span>
      <Badge>L{bundle.dashboard.level}</Badge>
      <Badge tone="warning">{bundle.dashboard.awaitingApproval} pending</Badge>
      {bundle.dashboard.needsIntervention ? (
        <Badge tone="danger">{bundle.dashboard.needsIntervention} alert</Badge>
      ) : (
        <Badge tone="success">ok</Badge>
      )}
      <Link
        to="/platform-builder/autonomy"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("auto_open")}
      >
        Center →
      </Link>
    </div>
  );
}
