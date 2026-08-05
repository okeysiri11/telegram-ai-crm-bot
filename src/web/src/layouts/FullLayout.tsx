import type { ReactNode } from "react";
import { lazy, Suspense, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { Sidebar } from "@/navigation/Sidebar";
import { TopNavigation } from "@/navigation/TopNavigation";
import { GlobalWorkspaceBar, UnifiedToastStrip } from "@/workspace-chrome";
import { registerIntegrationSearch } from "@/integration-hub";
import { OfflineBanner } from "@/launch";
import { AiOsExperienceChrome } from "@/ai-os-chrome";
import { EnterpriseIntelligenceLayer } from "@/enterprise-intelligence";
import { AITeamCollaborationWorkspace } from "@/ai-team-collaboration";
import { WorkflowAutomationWorkspace } from "@/enterprise-workflow";
import { DecisionContinueBar } from "@/decision-flow";
import { ActivityPanel, BottomDock, LeftDock, ShellRuntimeBar } from "@/shell/enterprise";
import { rememberModuleRoute } from "@/modules/lastModuleStore";
import { WorkspaceTabBar } from "@/workspace-engine/WorkspaceTabBar";
import { QuickCreateButton } from "@/workspace-engine/QuickCreateButton";
import { useWorkspaceRouteSync } from "@/workspace-engine/useWorkspaceTabs";
import { useEnterpriseKeyboard } from "@/command-center-runtime/useEnterpriseKeyboard";

/**
 * Sprint 1.1.1 — strips load from strip-only modules (not page barrels),
 * so App route `lazy()` for full pages is no longer defeated by FullLayout.
 */
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

const OPS_KEY = "ewp_ops_strips_open_v1";

function StripFallback() {
  return <div className="eds-type-helper px-1 py-0.5 text-[var(--eds-text-muted)]" aria-hidden />;
}

/**
 * Sprint 27.1 — Application Shell:
 * Top Header · Left Sidebar · Main Workspace · Right Activity · Bottom Status.
 * Full-viewport layout for Full HD → 4K / ultrawide.
 */
export function FullLayout({ children }: { children: ReactNode }) {
  const loc = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [opsOpen, setOpsOpen] = useState(() => {
    try {
      return localStorage.getItem(OPS_KEY) === "1";
    } catch {
      return false;
    }
  });

  useWorkspaceRouteSync();
  useEnterpriseKeyboard();

  useEffect(() => {
    registerIntegrationSearch();
  }, []);

  useEffect(() => {
    rememberModuleRoute(loc.pathname);
  }, [loc.pathname]);

  function toggleOps() {
    setOpsOpen((v) => {
      const next = !v;
      try {
        localStorage.setItem(OPS_KEY, next ? "1" : "0");
      } catch {
        /* ignore */
      }
      return next;
    });
  }

  return (
    <div className="ews-shell eds-shell">
      <div className="ews-shell-body">
        <Sidebar mobileOpen={mobileOpen} onNavigate={() => setMobileOpen(false)} />
        <LeftDock />
        <div className="ews-workspace">
          <TopNavigation onMenuToggle={() => setMobileOpen((v) => !v)} />
          <main className="ews-main eds-main">
            <div className="eds-page">
              <OfflineBanner />
              <GlobalWorkspaceBar />
              <WorkspaceTabBar />
              <AiOsExperienceChrome />
              <EnterpriseIntelligenceLayer compact />
              <AITeamCollaborationWorkspace compact />
              <WorkflowAutomationWorkspace compact />
              <Suspense fallback={<StripFallback />}>
                <ControlTowerStrip />
                <GovernanceStrip />
                <LearningStrip />
              </Suspense>
              <div className="eds-ops-chrome">
                <button type="button" className="eds-ops-chrome-toggle edm-press" onClick={toggleOps}>
                  {opsOpen ? "Hide platform strips" : "Show platform strips"}
                </button>
                {opsOpen ? (
                  <div className="eds-ops-chrome-body edm-card-expand">
                    <Suspense fallback={<StripFallback />}>
                      <AIBuilderStudioStrip />
                      <MarketplaceStrip />
                      <EnterpriseTwinStrip />
                      <IntegrationHubStrip />
                      <AIRuntimeStrip />
                      <DataFabricStrip />
                      <PredictiveStrip />
                      <AutonomyStrip />
                      <OkrStrip />
                    </Suspense>
                  </div>
                ) : null}
              </div>
              <UnifiedToastStrip />
              <DecisionContinueBar />
              <div key={loc.pathname} className="edm-page">
                {children}
              </div>
            </div>
          </main>
          <BottomDock />
        </div>
        <ActivityPanel />
      </div>
      <QuickCreateButton />
      <ShellRuntimeBar />
    </div>
  );
}
