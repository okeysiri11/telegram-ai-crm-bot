/**
 * Sprint 41.3 / 42.3 — self-explaining landings;
 * Auto uses Human-First layout (AI-first, zero learning curve).
 */

import type { ReactNode } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { MODULE_LANDINGS } from "./moduleLandingCatalog";
import { ModuleLandingView } from "./ModuleLandingView";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { AutoHumanLandingView } from "@/human-first";
import { useIsMobile } from "@/shell/mobile/useIsMobile";

/** On phone these open the live ops cabinet, not the catalog landing (menu A). */
const MOBILE_OPS_CABINET_LANDINGS = new Set(["agro", "auto", "cafe", "legal", "crypto", "drone", "recruiting"]);

/** Agro Command Center is the desktop home — refresh must not bounce to the catalog landing. */
const ALWAYS_OPS_CABINET_LANDINGS = new Set(["agro", "recruiting"]);

export function WorkspaceLandingGate({
  landingId,
  children,
}: {
  landingId: string;
  children: ReactNode;
}) {
  const isMobile = useIsMobile();
  const [params] = useSearchParams();
  const { sub } = useParams<{ sub?: string }>();
  const landing = MODULE_LANDINGS.find((m) => m.id === landingId);
  const deep =
    Boolean(sub) ||
    Boolean(params.get("view")) ||
    Boolean(params.get("action")) ||
    params.get("demo") === "1";

  if (ALWAYS_OPS_CABINET_LANDINGS.has(landingId) || (isMobile && MOBILE_OPS_CABINET_LANDINGS.has(landingId))) {
    return <>{children}</>;
  }

  if (landing && !deep) {
    return (
      <WorkspaceLayout>
        {landingId === "auto" ? (
          <AutoHumanLandingView landing={landing} />
        ) : (
          <ModuleLandingView landing={landing} />
        )}
      </WorkspaceLayout>
    );
  }

  return <>{children}</>;
}
