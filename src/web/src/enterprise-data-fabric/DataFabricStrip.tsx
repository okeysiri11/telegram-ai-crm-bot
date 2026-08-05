/** Data Fabric strip — Sprint 1.1.1. */

import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Badge } from "@/ui";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { telemetry } from "@/integrations/telemetry";
import { deriveDataFabric } from "./deriveFabric";

export function DataFabricStrip() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const fabric = useMemo(() => deriveDataFabric(snapshot, { notifications }), [snapshot, notifications]);
  return (
    <div className="edf-strip" aria-label="Data Fabric">
      <span className="edf-strip-label">Data Fabric</span>
      <Badge>{fabric.executive.linkedObjects} links</Badge>
      {fabric.executive.problemLinks ? (
        <Badge tone="warning">{fabric.executive.problemLinks} issues</Badge>
      ) : (
        <Badge tone="success">healthy</Badge>
      )}
      <Link
        to="/platform-builder/data-fabric"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("fabric_open")}
      >
        Graph →
      </Link>
    </div>
  );
}
