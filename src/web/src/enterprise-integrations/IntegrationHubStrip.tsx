/** Integration Hub strip — Sprint 1.1.1. */

import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Badge } from "@/ui";
import { useLiveEnterprise } from "@/live-ops";
import { telemetry } from "@/integrations/telemetry";
import { deriveIntegrationHub } from "./deriveIntegrations";

export function IntegrationHubStrip() {
  const { snapshot } = useLiveEnterprise(true);
  const bundle = useMemo(() => deriveIntegrationHub(snapshot), [snapshot]);
  return (
    <div className="eih-strip" aria-label="Integration Hub">
      <span className="eih-strip-label">Integrations</span>
      <Badge tone="success">{bundle.dashboard.active} active</Badge>
      {bundle.dashboard.needsSetup ? (
        <Badge tone="warning">{bundle.dashboard.needsSetup} setup</Badge>
      ) : null}
      {bundle.dashboard.errors ? (
        <Badge tone="danger">{bundle.dashboard.errors} err</Badge>
      ) : (
        <Badge>ok</Badge>
      )}
      <Link
        to="/platform-builder/integrations"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("int_hub_open")}
      >
        Hub →
      </Link>
    </div>
  );
}
