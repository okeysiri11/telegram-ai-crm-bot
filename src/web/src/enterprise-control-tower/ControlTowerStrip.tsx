/**
 * Control Tower chrome strip — Sprint 1.1.1.
 * Separate from EnterpriseControlTowerPage so App can lazy the page without
 * FullLayout statically pulling the full Control Tower surface.
 */

import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Badge } from "@/ui";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { telemetry } from "@/integrations/telemetry";
import { deriveControlTower } from "./deriveControlTower";

export function ControlTowerStrip() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const first = loadFirstEntry();
  const tower = useMemo(
    () =>
      deriveControlTower(snapshot, {
        company: first.companyName,
        notifications,
        roleId: first.roleId,
      }),
    [snapshot, first.companyName, first.roleId, notifications],
  );
  const risks = tower.incidents.filter((i) => i.severity === "error" || i.severity === "overload").length;
  return (
    <div className="ect-strip" aria-label="Control Tower">
      <span className="ect-strip-label">Control Tower</span>
      <Badge tone="success">{tower.overview.find((o) => o.id === "runtime")?.value || "0"} runtime</Badge>
      {risks ? <Badge tone="danger">{risks} incidents</Badge> : <Badge>stable</Badge>}
      <Link
        to="/platform-builder/control-tower"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("ect_open")}
      >
        Tower →
      </Link>
    </div>
  );
}
