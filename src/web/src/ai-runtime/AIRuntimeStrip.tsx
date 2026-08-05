/** AI Runtime strip — Sprint 1.1.1. */

import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Badge } from "@/ui";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { telemetry } from "@/integrations/telemetry";
import { deriveRuntime } from "./deriveRuntime";

export function AIRuntimeStrip() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const rt = useMemo(() => deriveRuntime(snapshot, notifications), [snapshot, notifications]);
  return (
    <div className="art-strip" aria-label="AI Runtime">
      <span className="art-strip-label">Runtime</span>
      <Badge tone="success">{rt.counts.active} active</Badge>
      <Badge tone="warning">{rt.health.queueSize} queue</Badge>
      {rt.health.failedTasks ? (
        <Badge tone="danger">{rt.health.failedTasks} fail</Badge>
      ) : (
        <Badge>ok</Badge>
      )}
      <Link
        to="/platform-builder/runtime"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("runtime_open")}
      >
        Center →
      </Link>
    </div>
  );
}
