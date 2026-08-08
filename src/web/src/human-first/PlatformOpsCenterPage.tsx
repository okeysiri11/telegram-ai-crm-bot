/**
 * Sprint 42.3 — Owner/Developer Platform Control Center.
 * Engineering strips live here — not on everyday Auto / CRM screens.
 */

import { lazy, Suspense } from "react";
import { Link } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Card } from "@/ui";
import { AiOsExperienceChrome } from "@/ai-os-chrome";
import { EnterpriseIntelligenceLayer } from "@/enterprise-intelligence";
import { AITeamCollaborationWorkspace } from "@/ai-team-collaboration";
import { WorkflowAutomationWorkspace } from "@/enterprise-workflow";

const ControlTowerStrip = lazy(() =>
  import("@/enterprise-control-tower/ControlTowerStrip").then((m) => ({ default: m.ControlTowerStrip })),
);
const GovernanceStrip = lazy(() =>
  import("@/enterprise-governance/GovernanceStrip").then((m) => ({ default: m.GovernanceStrip })),
);
const LearningStrip = lazy(() =>
  import("@/self-learning-enterprise/LearningStrip").then((m) => ({ default: m.LearningStrip })),
);
const AIBuilderStudioStrip = lazy(() =>
  import("@/ai-builder-studio/AIBuilderStudioStrip").then((m) => ({ default: m.AIBuilderStudioStrip })),
);
const MarketplaceStrip = lazy(() =>
  import("@/enterprise-marketplace/MarketplaceStrip").then((m) => ({ default: m.MarketplaceStrip })),
);
const EnterpriseTwinStrip = lazy(() =>
  import("@/enterprise-twin/EnterpriseTwinStrip").then((m) => ({ default: m.EnterpriseTwinStrip })),
);
const IntegrationHubStrip = lazy(() =>
  import("@/enterprise-integrations/IntegrationHubStrip").then((m) => ({ default: m.IntegrationHubStrip })),
);
const AIRuntimeStrip = lazy(() =>
  import("@/ai-runtime/AIRuntimeStrip").then((m) => ({ default: m.AIRuntimeStrip })),
);
const DataFabricStrip = lazy(() =>
  import("@/enterprise-data-fabric/DataFabricStrip").then((m) => ({ default: m.DataFabricStrip })),
);
const PredictiveStrip = lazy(() =>
  import("@/predictive-intelligence/PredictiveStrip").then((m) => ({ default: m.PredictiveStrip })),
);
const AutonomyStrip = lazy(() =>
  import("@/autonomous-enterprise/AutonomyStrip").then((m) => ({ default: m.AutonomyStrip })),
);
const OkrStrip = lazy(() =>
  import("@/enterprise-okr/OkrStrip").then((m) => ({ default: m.OkrStrip })),
);

function StripFallback() {
  return <p className="eds-type-helper px-1 py-2">Загрузка панели…</p>;
}

export function PlatformOpsCenterPage() {
  return (
    <WorkspaceLayout>
      <div className="space-y-4" data-testid="platform-ops-center">
        <header className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <Badge tone="warning">Owner · Developer</Badge>
            <h1 className="eds-type-title mt-2 text-2xl">Центр управления платформой</h1>
            <p className="mt-1 eds-type-body text-[var(--eds-text-muted)]">
              Инженерные панели: Builder, Marketplace, Twin, Runtime, Predictive, Data Fabric,
              Integrations, Autonomy. Не показываются в обычной работе модулей.
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <Link to="/platform-builder" className="eds-type-caption text-[var(--eds-accent)]">
              ← Платформа
            </Link>
            <Link to="/platform-builder/hercules" className="eds-type-caption text-[var(--eds-accent)]">
              Hercules Control Center →
            </Link>
          </div>
        </header>

        <Card title="AI Concierge · Intelligence · Team · Workflows">
          <AiOsExperienceChrome />
          <div className="mt-3 space-y-3">
            <EnterpriseIntelligenceLayer compact />
            <AITeamCollaborationWorkspace compact />
            <WorkflowAutomationWorkspace compact />
          </div>
        </Card>

        <Card title="Control Tower · Governance · Learning">
          <Suspense fallback={<StripFallback />}>
            <ControlTowerStrip />
            <GovernanceStrip />
            <LearningStrip />
          </Suspense>
        </Card>

        <Card title="Ops strips">
          <Suspense fallback={<StripFallback />}>
            <div className="space-y-2">
              <AIBuilderStudioStrip />
              <MarketplaceStrip />
              <EnterpriseTwinStrip />
              <IntegrationHubStrip />
              <AIRuntimeStrip />
              <DataFabricStrip />
              <PredictiveStrip />
              <AutonomyStrip />
              <OkrStrip />
            </div>
          </Suspense>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
