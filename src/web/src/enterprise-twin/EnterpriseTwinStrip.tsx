/** Enterprise Twin strip — Sprint 1.1.1. */

import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Badge } from "@/ui";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { telemetry } from "@/integrations/telemetry";
import { deriveEnterpriseTwin } from "./deriveTwin";

export function EnterpriseTwinStrip() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const first = loadFirstEntry();
  const twin = useMemo(
    () =>
      deriveEnterpriseTwin(snapshot, {
        company: first.companyName,
        notifications,
        roleId: first.roleId,
      }),
    [snapshot, first.companyName, first.roleId, notifications],
  );
  const hot = twin.heatmap[0];
  const risks = twin.executive.risks.length;

  return (
    <div className="etwin-strip" aria-label="Enterprise Twin">
      <span className="etwin-strip-label">Twin</span>
      <Badge>{twin.nodes.length} nodes</Badge>
      {hot ? <Badge tone={hot.tone === "risk" ? "danger" : "success"}>{hot.label}</Badge> : null}
      {risks ? <Badge tone="warning">{risks} risks</Badge> : <Badge tone="success">stable</Badge>}
      <Link
        to="/enterprise-twin"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("twin_open")}
      >
        Org →
      </Link>
    </div>
  );
}
