/** AI Builder Studio strip — Sprint 1.1.1. */

import { Link } from "react-router-dom";
import { Badge } from "@/ui";
import { telemetry } from "@/integrations/telemetry";
import { studioCatalogStats } from "./studioCatalog";

export function AIBuilderStudioStrip() {
  const stats = studioCatalogStats();
  return (
    <div className="abs-strip" aria-label="AI Builder Studio">
      <span className="abs-strip-label">Builder</span>
      <Badge>{stats.skills} skills</Badge>
      <Badge>{stats.workflows} wf</Badge>
      <Badge>{stats.templates} tpl</Badge>
      <Link
        to="/platform-builder/builder-studio"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open")}
      >
        Studio →
      </Link>
      <Link
        to="/automation"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_automation")}
      >
        Automation →
      </Link>
      <Link
        to="/business-network"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_ebn")}
      >
        Network →
      </Link>
      <Link
        to="/digital-citizens"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_citizens")}
      >
        Citizens →
      </Link>
      <Link
        to="/life-engine"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_life")}
      >
        Life →
      </Link>
      <Link
        to="/assets"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_assets")}
      >
        Assets →
      </Link>
      <Link
        to="/spatial"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_spatial")}
      >
        Spatial →
      </Link>
      <Link
        to="/city-visualization"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_city_viz")}
      >
        Viz →
      </Link>
      <Link
        to="/interactions"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_interactions")}
      >
        Interact →
      </Link>
      <Link
        to="/intelligence"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_intelligence")}
      >
        Intel →
      </Link>
      <Link
        to="/orchestrator"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_orchestrator")}
      >
        Orch →
      </Link>
      <Link
        to="/kernel"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_kernel")}
      >
        Kernel →
      </Link>
    </div>
  );
}
