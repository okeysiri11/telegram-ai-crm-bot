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

export function WorkspaceLandingGate({
  landingId,
  children,
}: {
  landingId: string;
  children: ReactNode;
}) {
  const [params] = useSearchParams();
  const { sub } = useParams<{ sub?: string }>();
  const landing = MODULE_LANDINGS.find((m) => m.id === landingId);
  const deep =
    Boolean(sub) ||
    Boolean(params.get("view")) ||
    Boolean(params.get("action")) ||
    params.get("demo") === "1";

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
