/** Predictive strip — Sprint 1.1.1. */

import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Badge } from "@/ui";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { telemetry } from "@/integrations/telemetry";
import { derivePredictive } from "./derivePredictive";

export function PredictiveStrip() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const pred = useMemo(() => derivePredictive(snapshot, notifications), [snapshot, notifications]);
  const top = pred.forecasts[0];
  const highRisks = pred.risks.filter((r) => r.severity === "high").length;

  return (
    <div className="pred-strip" aria-label="Predictive Intelligence">
      <span className="pred-strip-label">Predictive</span>
      {top ? (
        <Badge tone={top.tone === "risk" ? "danger" : "success"}>
          KPI {top.current}→{top.forecast}
        </Badge>
      ) : null}
      {highRisks ? <Badge tone="danger">{highRisks} risks</Badge> : <Badge tone="success">stable</Badge>}
      <Link
        to="/platform-builder/predictive"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("pred_open")}
      >
        Forecast →
      </Link>
    </div>
  );
}
