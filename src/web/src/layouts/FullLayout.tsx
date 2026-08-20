import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Sidebar } from "@/navigation/Sidebar";
import { TopNavigation } from "@/navigation/TopNavigation";
import { WorkspaceQuickDock, UnifiedToastStrip } from "@/workspace-chrome";
import { registerIntegrationSearch } from "@/integration-hub";
import { OfflineBanner } from "@/launch";
import { DecisionContinueBar } from "@/decision-flow";
import { ActivityPanel, BottomDock, LeftDock, ShellRuntimeBar } from "@/shell/enterprise";
import { rememberModuleRoute } from "@/modules/lastModuleStore";
import { WorkspaceTabBar } from "@/workspace-engine/WorkspaceTabBar";
import {
  shouldShowWorkspaceTabBar,
  useWorkspaceTabChromeStore,
} from "@/workspace-engine/workspaceTabChromeStore";
import { QuickCreateButton } from "@/workspace-engine/QuickCreateButton";
import { useWorkspaceRouteSync } from "@/workspace-engine/useWorkspaceTabs";
import { useEnterpriseKeyboard } from "@/command-center-runtime/useEnterpriseKeyboard";
import { ViewModeRouteGuard, useViewModeStore, useExperienceModeStore } from "@/ux-revolution";
import { useI18n } from "@/i18n";
import { PageOrientationBar } from "@/help/PageOrientationBar";
import { WorkspaceSlotBanner } from "@/multi-role/WorkspaceSlotBanner";
import { useAdaptiveShellStore } from "@/shell/enterprise/adaptiveShellStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { MobileChrome, useIsMobile } from "@/shell/mobile";

/**
 * Sprint 27.1 / 42.3 / 42.6 — Application Shell.
 * Human-First: engineering strips / Intelligence / Concierge are NOT inline.
 * Sprint 42.6: workspace tab strip removed from Owner/Admin/Manager/Client;
 * Developer may enable it manually (technical panel).
 */
export function FullLayout({ children }: { children: ReactNode }) {
  const loc = useLocation();
  const t = useI18n((s) => s.t);
  void t;
  const viewMode = useViewModeStore((s) => s.viewMode);
  const experienceMode = useExperienceModeStore((s) => s.mode);
  const tabChromeEnabled = useWorkspaceTabChromeStore((s) => s.enabled);
  /** Everyday business chrome — hide platform engineering panels */
  const isHumanWorkMode =
    viewMode === "client" ||
    viewMode === "manager" ||
    viewMode === "company_admin" ||
    experienceMode === "simple";
  const showOwnerDevChrome =
    (viewMode === "platform_owner" || viewMode === "developer") && experienceMode === "pro";
  const isClientChrome = viewMode === "client" || viewMode === "manager";
  const showWorkspaceTabs = shouldShowWorkspaceTabBar(viewMode, tabChromeEnabled);
  const activeRoleId = useRoleSwitcher((s) => s.activeRoleId);
  const focusMode = useAdaptiveShellStore((s) => s.focusMode);
  const [mobileOpen, setMobileOpen] = useState(false);
  const isMobile = useIsMobile();

  useWorkspaceRouteSync();
  useEnterpriseKeyboard();

  useEffect(() => {
    useAdaptiveShellStore.getState().hydrateForRole(activeRoleId);
  }, [activeRoleId]);

  useEffect(() => {
    registerIntegrationSearch();
  }, []);

  useEffect(() => {
    rememberModuleRoute(loc.pathname);
  }, [loc.pathname]);

  return (
    <div
      className="ews-shell eds-shell"
      data-view-mode={viewMode}
      data-experience-mode={experienceMode}
      data-human-work={isHumanWorkMode ? "1" : "0"}
      data-focus-mode={focusMode ? "1" : "0"}
      data-workspace-tabs={showWorkspaceTabs ? "1" : "0"}
    >
      <ViewModeRouteGuard />
      <div className="ews-shell-body">
        <Sidebar mobileOpen={!isMobile && mobileOpen} onNavigate={() => setMobileOpen(false)} />
        {!isClientChrome && !isMobile ? <LeftDock /> : null}
        <div className="ews-workspace">
          {isMobile ? <MobileChrome /> : <TopNavigation onMenuToggle={() => setMobileOpen((v) => !v)} />}
          <main className="ews-main eds-main">
            <div className="eds-page">
              <OfflineBanner />
              <WorkspaceSlotBanner />
              {!isMobile ? <WorkspaceQuickDock /> : null}
              {showWorkspaceTabs ? <WorkspaceTabBar /> : null}
              {showOwnerDevChrome && !isMobile ? (
                <div
                  className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-md border border-[var(--ew-border)] px-3 py-2"
                  data-testid="owner-ops-hint"
                >
                  <p className="eds-type-helper">
                    Инженерные панели перенесены в{" "}
                    <Link to="/platform-builder/ops-center" className="font-medium text-[var(--eds-accent)]">
                      Платформа → Центр управления
                    </Link>
                  </p>
                  <Link
                    to="/platform-builder/ops-center"
                    className="eds-type-caption font-medium text-[var(--eds-accent)]"
                  >
                    Открыть
                  </Link>
                </div>
              ) : null}
              <UnifiedToastStrip />
              {!isHumanWorkMode ? <DecisionContinueBar /> : null}
              {!isHumanWorkMode ? <PageOrientationBar /> : null}
              <div key={loc.pathname} className="edm-page">
                {children}
              </div>
            </div>
          </main>
          {!isClientChrome && !isMobile ? <BottomDock /> : null}
        </div>
        <ActivityPanel />
      </div>
      {!isClientChrome && !isMobile ? <QuickCreateButton /> : null}
      {showOwnerDevChrome && !isMobile ? <ShellRuntimeBar /> : null}
    </div>
  );
}
