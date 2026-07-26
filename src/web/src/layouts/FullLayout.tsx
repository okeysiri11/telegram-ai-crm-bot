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

/** Shared application shell — sidebar + top nav + unified workspace + AI OS chrome. */
export function FullLayout({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    registerUnifiedWorkspaceSearch();
  }, []);

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
            <AIBuilderStudioStrip />
            <UnifiedToastStrip />
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
