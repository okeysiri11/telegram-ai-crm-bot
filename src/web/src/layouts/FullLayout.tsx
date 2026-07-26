import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { Sidebar } from "@/navigation/Sidebar";
import { TopNavigation } from "@/navigation/TopNavigation";
import { GlobalWorkspaceBar, UnifiedToastStrip, registerUnifiedWorkspaceSearch } from "@/workspace-chrome";
import { OfflineBanner } from "@/launch";
import { AiOsExperienceChrome } from "@/ai-os-chrome";
import { EnterpriseIntelligenceLayer } from "@/enterprise-intelligence";
import { AITeamCollaborationWorkspace } from "@/ai-team-collaboration";
import { WorkflowAutomationWorkspace } from "@/enterprise-workflow";
import { AIBuilderStudioStrip } from "@/ai-builder-studio";
import { MarketplaceStrip } from "@/enterprise-marketplace";
import { EnterpriseTwinStrip } from "@/enterprise-twin";
import { IntegrationHubStrip } from "@/enterprise-integrations";
import { AIRuntimeStrip } from "@/ai-runtime";
import { DataFabricStrip } from "@/enterprise-data-fabric";
import { PredictiveStrip } from "@/predictive-intelligence";
import { AutonomyStrip } from "@/autonomous-enterprise";
import { ControlTowerStrip } from "@/enterprise-control-tower";
import { LearningStrip } from "@/self-learning-enterprise";
import { OkrStrip } from "@/enterprise-okr";
import { GovernanceStrip } from "@/enterprise-governance";

const OPS_KEY = "ewp_ops_strips_open_v1";

/** Shared application shell — sidebar + top nav + unified workspace + AI OS chrome. */
export function FullLayout({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [opsOpen, setOpsOpen] = useState(() => {
    try {
      return localStorage.getItem(OPS_KEY) === "1";
    } catch {
      return false;
    }
  });

  useEffect(() => {
    registerUnifiedWorkspaceSearch();
  }, []);

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
    <div className="flex min-h-full eds-shell">
      <Sidebar mobileOpen={mobileOpen} onNavigate={() => setMobileOpen(false)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopNavigation onMenuToggle={() => setMobileOpen((v) => !v)} />
        <main className="eds-main flex-1 p-4 md:p-6 xl:p-8">
          <div className="eds-page eds-anim-page">
            <OfflineBanner />
            <GlobalWorkspaceBar />
            <AiOsExperienceChrome />
            <EnterpriseIntelligenceLayer compact />
            <AITeamCollaborationWorkspace compact />
            <WorkflowAutomationWorkspace compact />
            {/* Sprint 34.0 RC — priority strips always on; secondary collapsed for render budget */}
            <ControlTowerStrip />
            <GovernanceStrip />
            <LearningStrip />
            <div className="eds-ops-chrome">
              <button type="button" className="eds-ops-chrome-toggle" onClick={toggleOps}>
                {opsOpen ? "Hide platform strips" : "Show platform strips"}
              </button>
              {opsOpen ? (
                <div className="eds-ops-chrome-body">
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
              ) : null}
            </div>
            <UnifiedToastStrip />
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
