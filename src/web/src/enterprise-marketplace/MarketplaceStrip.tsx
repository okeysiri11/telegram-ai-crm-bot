/** Marketplace strip — Sprint 1.1.1. */

import { Link } from "react-router-dom";
import { Badge } from "@/ui";
import { telemetry } from "@/integrations/telemetry";
import { MARKETPLACE_SOLUTIONS } from "./solutionCatalog";

export function MarketplaceStrip() {
  const n = MARKETPLACE_SOLUTIONS.length;
  const packs = MARKETPLACE_SOLUTIONS.filter((s) => s.enterprisePack).length;
  return (
    <div className="mkt-strip" aria-label="Marketplace">
      <span className="mkt-strip-label">Marketplace</span>
      <Badge>{n} solutions</Badge>
      <Badge tone="success">{packs} packs</Badge>
      <Link
        to="/platform-builder/solution-hub"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("mkt_open")}
      >
        Hub →
      </Link>
    </div>
  );
}
