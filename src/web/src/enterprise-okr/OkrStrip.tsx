/** OKR strip — Sprint 1.1.1. */

import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Badge } from "@/ui";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { telemetry } from "@/integrations/telemetry";
import { deriveOkr } from "./deriveOkr";

export function OkrStrip() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const okr = useMemo(() => deriveOkr(snapshot, notifications), [snapshot, notifications]);
  return (
    <div className="okr-strip" aria-label="OKR">
      <span className="okr-strip-label">OKR</span>
      <Badge tone="success">{okr.mc.progressAvg}%</Badge>
      {okr.mc.riskCount ? (
        <Badge tone="danger">{okr.mc.riskCount} risk</Badge>
      ) : (
        <Badge>stable</Badge>
      )}
      <Link
        to="/platform-builder/okr"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("okr_open")}
      >
        Goals →
      </Link>
    </div>
  );
}
