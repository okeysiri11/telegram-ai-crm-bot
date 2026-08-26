import { Navigate, Route, Routes } from "react-router-dom";
import { lazy, Suspense } from "react";
import { ProtectedRoute } from "@/shell/ProtectedRoute";
import { CasinoBrowseRoute } from "@/shell/CasinoBrowseRoute";
import { LoadingScreen } from "@/shell/LoadingScreen";
import { RouteErrorBoundary } from "@/shell/RouteErrorBoundary";
import { DashboardPage } from "@/pages/DashboardPage";
import { OwnerDashboardPage } from "@/navigation/OwnerDashboardPage";
import { ClientDashboardPage } from "@/dashboard/ClientDashboardPage";
import { DealerDashboardPage } from "@/dashboard/DealerDashboardPage";
import { AdminDashboardPage } from "@/dashboard/AdminDashboardPage";
import { ManagerDashboardPage, EmployeeDashboardPage } from "@/dashboard/RoleOpsDashboards";
import { TasksPage } from "@/enterprise-workspace";
import { CalendarModulePage, NotificationsModulePage } from "@/enterprise-business";
import { InvitationPage } from "@/pages/InvitationPage";
import { homeRouteForRole } from "@/navigation/roleHome";
import { wsKey } from "@/multi-role/workspaceSlot";
import { ClientOnboardingPage } from "@/multi-role/ClientOnboardingPage";
import { CryptoPayoutConfirmPanel } from "@/crypto-antifraud/CryptoPayoutConfirmPanel";
import { PilotDashboardPage } from "@/pages/PilotDashboardPage";
import { ProductionReadinessPage } from "@/pages/ProductionReadinessPage";
import { ExternalPilotOnboardPage } from "@/pages/ExternalPilotOnboardPage";
import { PilotInvitePage } from "@/pages/PilotInvitePage";
import { InviteAcceptPage } from "@/pages/InviteAcceptPage";
import { PilotExecutionPage } from "@/pages/PilotExecutionPage";
import { FirstEntryPage } from "@/onboarding/FirstEntryPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { DemoScenarioPage } from "@/demo";
import { ModulePageById, SearchWorkspacePage, WorkspaceLandingGate } from "@/modules";
import { useLastModuleStore } from "@/modules/lastModuleStore";
import { DesktopShell } from "@/enterprise-desktop";
import { PlatformOpsCenterPage } from "@/human-first";
import { HerculesControlCenterPage } from "@/hercules";
import { AiCommandCenterPage } from "@/ai-command";
import { ModeSettingsPage } from "@/platform-modes";
import { AiWorkspacePage } from "@/ai-workspace";
import { AutomationCenterPage45 } from "@/universal-automation";
import { VerticalWorkspacePage } from "@/vertical-workspace";
import { AiTasksPage } from "@/owner-experience";

const CommandRuntimeInspectorPage = lazy(() =>
  import("@/runtime/commandRuntime/CommandRuntimeInspectorPage").then((m) => ({
    default: m.CommandRuntimeInspectorPage,
  })),
);
const WorkflowRuntimeInspectorPage = lazy(() =>
  import("@/runtime/workflowRuntime/WorkflowRuntimeInspectorPage").then((m) => ({
    default: m.WorkflowRuntimeInspectorPage,
  })),
);
const AutomationCenterPage = lazy(() =>
  import("@/runtime/automation/AutomationCenterPage").then((m) => ({
    default: m.AutomationCenterPage,
  })),
);
const BusinessNetworkPage = lazy(() =>
  import("@/runtime/businessNetwork/BusinessNetworkPage").then((m) => ({
    default: m.BusinessNetworkPage,
  })),
);
const DigitalCitizenPage = lazy(() =>
  import("@/runtime/digitalCitizen/DigitalCitizenPage").then((m) => ({
    default: m.DigitalCitizenPage,
  })),
);
const LifeEnginePage = lazy(() =>
  import("@/runtime/lifeEngine/LifeEnginePage").then((m) => ({
    default: m.LifeEnginePage,
  })),
);
const AssetRuntimePage = lazy(() =>
  import("@/runtime/assetRuntime/AssetRuntimePage").then((m) => ({
    default: m.AssetRuntimePage,
  })),
);
const SpatialRuntimePage = lazy(() =>
  import("@/runtime/spatialRuntime/SpatialRuntimePage").then((m) => ({
    default: m.SpatialRuntimePage,
  })),
);
const CityVisualizationPage = lazy(() =>
  import("@/runtime/cityVisualization/CityVisualizationPage").then((m) => ({
    default: m.CityVisualizationPage,
  })),
);
const InteractionRuntimePage = lazy(() =>
  import("@/runtime/interactionRuntime/InteractionRuntimePage").then((m) => ({
    default: m.InteractionRuntimePage,
  })),
);
const IntelligenceRuntimePage = lazy(() =>
  import("@/runtime/intelligenceRuntime/IntelligenceRuntimePage").then((m) => ({
    default: m.IntelligenceRuntimePage,
  })),
);
const OrchestratorPage = lazy(() =>
  import("@/runtime/orchestrator/OrchestratorPage").then((m) => ({
    default: m.OrchestratorPage,
  })),
);
const KernelPage = lazy(() =>
  import("@/runtime/kernel/KernelPage").then((m) => ({
    default: m.KernelPage,
  })),
);
function HomeRedirect() {
  const last = useLastModuleStore((s) => s.lastRoute);
  let roleId = "employee";
  try {
    roleId = localStorage.getItem(wsKey("ewp_role_switcher_v1")) || "employee";
  } catch {
    /* ignore */
  }
  const roleHome = homeRouteForRole(roleId);
  const target = last && last !== "/" && last !== "/login" ? last : roleHome;
  return <Navigate to={target} replace />;
}

/** Sprint 27.2 — protected module hub helper */
function Hub({ id }: { id: string }) {
  return (
    <ProtectedRoute>
      <RouteErrorBoundary zone={`Module:${id}`} recoveryHref="/dashboard">
        <ModulePageById id={id} />
      </RouteErrorBoundary>
    </ProtectedRoute>
  );
}

/** Sprint 1.1.1 — route-level lazy for heavy executive surfaces. */
const EnterpriseCityPage = lazy(() =>
  import("@/enterprise-city").then((m) => ({ default: m.EnterpriseCityPage })),
);
const CasinoApp = lazy(() =>
  import("@/casino").then((m) => ({ default: m.CasinoApp })),
);
const WorkflowCenterPage = lazy(() =>
  import("@/enterprise-workflow").then((m) => ({ default: m.WorkflowCenterPage })),
);
const AIBuilderStudioPage = lazy(() =>
  import("@/ai-builder-studio").then((m) => ({ default: m.AIBuilderStudioPage })),
);
const ServiceBuilderPage = lazy(() =>
  import("@/service-builder").then((m) => ({ default: m.ServiceBuilderPage })),
);
const EventBusPage = lazy(() =>
  import("@/event-bus").then((m) => ({ default: m.EventBusPage })),
);
const WorkflowRuntimeConsolePage = lazy(() =>
  import("@/workflow-runtime-console").then((m) => ({ default: m.WorkflowRuntimePage })),
);
const AIRuntimeConsolePage = lazy(() =>
  import("@/ai-runtime-console").then((m) => ({ default: m.AIRuntimeConsolePage })),
);
const ContextEnginePage = lazy(() =>
  import("@/context-engine-console").then((m) => ({ default: m.ContextEnginePage })),
);
const ProjectMemoryPage = lazy(() =>
  import("@/project-memory-console").then((m) => ({ default: m.ProjectMemoryPage })),
);
const VoiceCommandCenterPage = lazy(() =>
  import("@/voice-console").then((m) => ({ default: m.VoiceCommandCenterPage })),
);
const MultiAgentRuntimePage = lazy(() =>
  import("@/multi-agent-console").then((m) => ({ default: m.MultiAgentRuntimePage })),
);
const SkillsSdkPage = lazy(() =>
  import("@/skills-sdk-console").then((m) => ({ default: m.SkillsSdkPage })),
);
const CreativeFactoryPage = lazy(() =>
  import("@/creative-console").then((m) => ({ default: m.CreativeFactoryPage })),
);
const EnterpriseCityRuntimePage = lazy(() =>
  import("@/platform-console").then((m) => ({ default: m.EnterpriseCityRuntimePage })),
);
const AIProductionCenterPage = lazy(() =>
  import("@/ai-production-studio").then((m) => ({ default: m.AIProductionCenterPage })),
);
const AIStudioPage = lazy(() =>
  import("@/ai-studio").then((m) => ({ default: m.AIStudioPage })),
);
const EnterpriseMarketplacePage = lazy(() =>
  import("@/enterprise-marketplace").then((m) => ({ default: m.EnterpriseMarketplacePage })),
);
const EnterpriseIntegrationHubPage = lazy(() =>
  import("@/enterprise-integrations").then((m) => ({ default: m.EnterpriseIntegrationHubPage })),
);
const AIRuntimePage = lazy(() =>
  import("@/ai-runtime").then((m) => ({ default: m.AIRuntimePage })),
);
const AIAgentCenterPage = lazy(() =>
  import("@/ai-runtime").then((m) => ({ default: m.AIAgentCenterPage })),
);
const PlatformHealthPage = lazy(() =>
  import("@/platform-integration").then((m) => ({ default: m.PlatformHealthPage })),
);
const PlatformErrorPage = lazy(() =>
  import("@/platform-integration").then((m) => ({ default: m.PlatformErrorPage })),
);
const EnterpriseDataFabricPage = lazy(() =>
  import("@/enterprise-data-fabric").then((m) => ({ default: m.EnterpriseDataFabricPage })),
);
const PredictiveIntelligencePage = lazy(() =>
  import("@/predictive-intelligence").then((m) => ({ default: m.PredictiveIntelligencePage })),
);
const AutonomousEnterprisePage = lazy(() =>
  import("@/autonomous-enterprise").then((m) => ({ default: m.AutonomousEnterprisePage })),
);
const EnterpriseControlTowerPage = lazy(() =>
  import("@/enterprise-control-tower/EnterpriseControlTowerPage").then((m) => ({
    default: m.EnterpriseControlTowerPage,
  })),
);
const SelfLearningEnterprisePage = lazy(() =>
  import("@/self-learning-enterprise").then((m) => ({ default: m.SelfLearningEnterprisePage })),
);
const EnterpriseOkrPage = lazy(() =>
  import("@/enterprise-okr").then((m) => ({ default: m.EnterpriseOkrPage })),
);
const EnterpriseGovernancePage = lazy(() =>
  import("@/enterprise-governance").then((m) => ({ default: m.EnterpriseGovernancePage })),
);
const ConciergeBuilderPage = lazy(() =>
  import("../platform-builder/pages/ConciergeBuilderPage").then((m) => ({
    default: m.ConciergeBuilderPage,
  })),
);
const MissionControlPage = lazy(() =>
  import("../platform-builder/pages/MissionControlPage").then((m) => ({
    default: m.MissionControlPage,
  })),
);
import {
  AccountLockedPage,
  ActivityCenterPage,
  ChangePasswordPage,
  ForgotPasswordPage,
  IdentityCenterPage,
  LoginPage,
  RegisterPage,
  LogoutPage,
  MfaCenterPage,
  MfaChallengePage,
  OrganizationsPage,
  PermissionsPage,
  ProfileCenterPage,
  ResetPasswordPage,
  RolesPage,
  SecurityCenterPage,
  SessionExpiredPage,
  SessionsPage,
  UsersPage,
} from "../auth/pages";
import {
  DashboardsPage,
  LayoutEditorPage,
  WorkspaceHomePage,
  WorkspaceModulePage,
  WorkspaceSettingsPage,
  WorkspacesPage,
} from "../workspace/pages";
import { AutomotiveLiveWorkflowPage } from "../workspace/automotive/AutomotiveLiveWorkflowPage";
const AutoBusinessPage = lazy(() =>
  import("../workspace/auto/AutoBusinessPage").then((m) => ({ default: m.AutoBusinessPage })),
);
const BeautyBusinessPage = lazy(() =>
  import("../workspace/beauty/BeautyBusinessPage").then((m) => ({ default: m.BeautyBusinessPage })),
);
const CafeBusinessPage = lazy(() =>
  import("../workspace/cafe/CafeBusinessPage").then((m) => ({ default: m.CafeBusinessPage })),
);
const AgroBusinessPage = lazy(() =>
  import("../workspace/agro/AgroBusinessPage").then((m) => ({ default: m.AgroBusinessPage })),
);
const LawyerBusinessPage = lazy(() =>
  import("../workspace/legal/LawyerBusinessPage").then((m) => ({ default: m.LawyerBusinessPage })),
);
const CryptoOtcDeskPage = lazy(() =>
  import("../workspace/crypto/CryptoOtcDeskPage").then((m) => ({ default: m.CryptoOtcDeskPage })),
);
import { AgricultureLiveWorkflowPage } from "../workspace/agriculture/AgricultureLiveWorkflowPage";
import { LegalLiveWorkflowPage } from "../workspace/legal/LegalLiveWorkflowPage";
import { DroneLiveWorkflowPage } from "../workspace/drone/DroneLiveWorkflowPage";
import { NavigationDashboardPage } from "../navigation/pages";
import { CommandCenterPage } from "../command-center/pages";
import { ReleaseCandidatePage } from "../release/pages";
import { AIOSPage } from "../ai-os/pages";
import { OrganizationBrainPage } from "../organization-brain/pages";
import { VerticalFederationPage } from "../vertical-federation/pages";
import {
  CustomerPortalPage,
  EmployeePortalPage,
  OwnerPortalPage,
} from "../portals";
import {
  AITeamCenterPage,
  BuilderAcademyPage,
  CollaborativeAIPage,
  FrameBuilderPage,
  GodModePage,
  OperationsCenterPage,
  PlatformBuilderDashboard,
  TeamMapPage,
  UniversalFrameworkPage,
  VerticalBuilderPage,
  VisualBehaviorPage,
  RenderingEnginePage,
  ThemeEnginePage,
  AssetRegistryPage,
  SimulationEnginePage,
  DirectorEnginePage,
  StoryEnginePage,
  IntelligenceEnginePage,
  ExperienceEnginePage,
  WorkspaceOSPage,
  CommandCenterOSPage,
  NavigationIntelligencePage,
  WorkflowIntelligencePage,
  DigitalTwinPage,
  TwinIntelligencePage,
  StrategyEnginePage,
  BusinessEcosystemPage,
} from "../platform-builder/pages";

export function App() {
  return (
    <Suspense fallback={<LoadingScreen />}>
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/login" element={<LoginPage />} />
      <Route path="/auth/register" element={<RegisterPage />} />
      <Route path="/auth/invite" element={<InvitationPage />} />
      <Route path="/auth/invitation" element={<InvitationPage />} />
      <Route path="/auth/logout" element={<LogoutPage />} />
      <Route path="/auth/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/auth/reset-password" element={<ResetPasswordPage />} />
      <Route path="/auth/locked" element={<AccountLockedPage />} />
      <Route path="/auth/session-expired" element={<SessionExpiredPage />} />
      <Route path="/auth/access-denied" element={<PlatformErrorPage kind="403" />} />
      <Route path="/auth/unauthorized" element={<PlatformErrorPage kind="unauthorized" />} />
      <Route path="/auth/mfa" element={<MfaChallengePage />} />
      <Route
        path="/auth/change-password"
        element={
          <ProtectedRoute>
            <ChangePasswordPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <HomeRedirect />
          </ProtectedRoute>
        }
      />
      <Route
        path="/onboarding/first-entry"
        element={
          <ProtectedRoute>
            <FirstEntryPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/onboarding/client"
        element={
          <ProtectedRoute>
            <ClientOnboardingPage />
          </ProtectedRoute>
        }
      />
      {/* Sprint 48.1 — the minimal real Web crypto/OTC payout-confirmation
          surface, wired to the same canonical CryptoPayoutOrchestrator the
          Telegram bot calls. Server-side require_role(ADMINISTRATOR) is the
          real gate; ProtectedRoute here only requires an authenticated
          session. */}
      <Route
        path="/crypto-otc/payout/:dealId"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="CryptoPayoutConfirm" recoveryHref="/dashboard">
              <CryptoPayoutConfirmPanel />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="Dashboard" recoveryHref="/workspace">
              <DashboardPage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/owner"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="Owner" recoveryHref="/dashboard">
              <WorkspaceLandingGate landingId="owner">
                <OwnerDashboardPage />
              </WorkspaceLandingGate>
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboards/client"
        element={
          <ProtectedRoute>
            <ClientDashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboards/dealer"
        element={
          <ProtectedRoute>
            <DealerDashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <ProtectedRoute>
            <AdminDashboardPage />
          </ProtectedRoute>
        }
      />
      <Route path="/dashboards/admin" element={<Navigate to="/admin" replace />} />
      <Route
        path="/dashboards/manager"
        element={
          <ProtectedRoute>
            <ManagerDashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboards/employee"
        element={
          <ProtectedRoute>
            <EmployeeDashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/calendar"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="Calendar" recoveryHref="/dashboard">
              <CalendarModulePage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/tasks"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="Tasks" recoveryHref="/dashboard">
              <TasksPage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/notifications"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="Notifications" recoveryHref="/dashboard">
              <NotificationsModulePage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/desktop"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="Enterprise Desktop" recoveryHref="/dashboard">
              <DesktopShell />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route path="/crm" element={<Hub id="crm" />} />
      {/* Sprint 40.3 — ACC-40-004 top-level CRM aliases (no redesign) */}
      <Route path="/deals" element={<Navigate to="/crm?view=deals" replace />} />
      <Route path="/clients" element={<Navigate to="/crm?view=clients" replace />} />
      <Route path="/companies" element={<Navigate to="/crm?view=companies" replace />} />
      <Route path="/leads" element={<Navigate to="/crm?view=leads" replace />} />
      <Route path="/reports" element={<Navigate to="/analytics" replace />} />
      <Route path="/profile" element={<Navigate to="/identity/profile" replace />} />
      <Route path="/erp" element={<Hub id="erp" />} />
      <Route path="/projects" element={<Hub id="projects" />} />
      <Route
        path="/production-studio"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="AI Production Center" recoveryHref="/enterprise-city">
              <AIProductionCenterPage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route path="/production" element={<Navigate to="/production-studio" replace />} />
      <Route
        path="/ai-studio"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="AI Studio" recoveryHref="/production-studio">
              <AIStudioPage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai-agents"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="AI Agent Center" recoveryHref="/dashboard">
              <WorkspaceLandingGate landingId="ai">
                <AIAgentCenterPage />
              </WorkspaceLandingGate>
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route path="/ai" element={<Navigate to="/ai-agents" replace />} />
      <Route
        path="/health"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="Platform Health" recoveryHref="/dashboard">
              <PlatformHealthPage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route path="/platform-health" element={<Navigate to="/health" replace />} />
      <Route path="/errors/404" element={<PlatformErrorPage kind="404" />} />
      <Route path="/errors/403" element={<PlatformErrorPage kind="403" />} />
      <Route path="/errors/500" element={<PlatformErrorPage kind="500" />} />
      <Route path="/errors/offline" element={<PlatformErrorPage kind="offline" />} />
      <Route path="/errors/unauthorized" element={<PlatformErrorPage kind="unauthorized" />} />
      <Route path="/knowledge" element={<Hub id="knowledge" />} />
      <Route path="/support" element={<Navigate to="/knowledge?view=articles&q=support" replace />} />
      <Route path="/documents" element={<Hub id="documents" />} />
      <Route path="/analytics" element={<Hub id="analytics" />} />
      <Route path="/marketplace" element={<Hub id="marketplace" />} />
      <Route path="/automation-hub" element={<Hub id="automation" />} />
      <Route path="/integrations" element={<Hub id="integrations" />} />
      <Route path="/security" element={<Navigate to="/identity/security" replace />} />
      <Route
        path="/city"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="Enterprise City" recoveryHref="/dashboard">
              <EnterpriseCityPage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route path="/city-hub" element={<Hub id="city" />} />
      <Route
        path="/search"
        element={
          <ProtectedRoute>
            <SearchWorkspacePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/enterprise-city"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="Enterprise City" recoveryHref="/dashboard?mode=executive">
              <EnterpriseCityPage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/casino/*"
        element={
          <CasinoBrowseRoute>
            <RouteErrorBoundary zone="Casino" recoveryHref="/casino">
              <CasinoApp />
            </RouteErrorBoundary>
          </CasinoBrowseRoute>
        }
      />
      <Route
        path="/platform-builder/workflow-center"
        element={
          <ProtectedRoute>
            <WorkflowCenterPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/builder-studio"
        element={
          <ProtectedRoute>
            <AIBuilderStudioPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/service-builder"
        element={
          <ProtectedRoute>
            <ServiceBuilderPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/service-builder"
        element={
          <ProtectedRoute>
            <ServiceBuilderPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/event-bus"
        element={
          <ProtectedRoute>
            <EventBusPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/event-bus"
        element={
          <ProtectedRoute>
            <EventBusPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/workflows"
        element={
          <ProtectedRoute>
            <WorkflowRuntimeConsolePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workflows"
        element={
          <ProtectedRoute>
            <WorkflowRuntimeConsolePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/solution-hub"
        element={
          <ProtectedRoute>
            <EnterpriseMarketplacePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/enterprise-twin"
        element={
          <ProtectedRoute>
            <Navigate to="/platform-builder/digital-twin" replace />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/integrations"
        element={
          <ProtectedRoute>
            <EnterpriseIntegrationHubPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/runtime"
        element={
          <ProtectedRoute>
            <AIRuntimePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/ai-runtime"
        element={
          <ProtectedRoute>
            <AIRuntimeConsolePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/context-engine"
        element={
          <ProtectedRoute>
            <ContextEnginePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/project-memory"
        element={
          <ProtectedRoute>
            <ProjectMemoryPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/voice"
        element={
          <ProtectedRoute>
            <VoiceCommandCenterPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/multi-agent"
        element={
          <ProtectedRoute>
            <MultiAgentRuntimePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/skills"
        element={
          <ProtectedRoute>
            <SkillsSdkPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/creative"
        element={
          <ProtectedRoute>
            <CreativeFactoryPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform"
        element={
          <ProtectedRoute>
            <EnterpriseCityRuntimePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform/search"
        element={
          <ProtectedRoute>
            <EnterpriseCityRuntimePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform/health"
        element={
          <ProtectedRoute>
            <EnterpriseCityRuntimePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform/registry"
        element={
          <ProtectedRoute>
            <EnterpriseCityRuntimePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform/activity"
        element={
          <ProtectedRoute>
            <EnterpriseCityRuntimePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform/command"
        element={
          <ProtectedRoute>
            <EnterpriseCityRuntimePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform/settings"
        element={
          <ProtectedRoute>
            <EnterpriseCityRuntimePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/skills-sdk"
        element={
          <ProtectedRoute>
            <SkillsSdkPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/creative-factory"
        element={
          <ProtectedRoute>
            <CreativeFactoryPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/multi-agent"
        element={
          <ProtectedRoute>
            <MultiAgentRuntimePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/voice-center"
        element={
          <ProtectedRoute>
            <VoiceCommandCenterPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/project-memory"
        element={
          <ProtectedRoute>
            <ProjectMemoryPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/context-engine"
        element={
          <ProtectedRoute>
            <ContextEnginePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai-runtime"
        element={
          <ProtectedRoute>
            <AIRuntimeConsolePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/data-fabric"
        element={
          <ProtectedRoute>
            <EnterpriseDataFabricPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/predictive"
        element={
          <ProtectedRoute>
            <PredictiveIntelligencePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/autonomy"
        element={
          <ProtectedRoute>
            <AutonomousEnterprisePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/control-tower"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="Control Tower" recoveryHref="/dashboard?mode=executive">
              <EnterpriseControlTowerPage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/ops-center"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="Platform Ops Center" recoveryHref="/platform-builder">
              <PlatformOpsCenterPage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/hercules"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="Hercules Control Center" recoveryHref="/platform-builder/ops-center">
              <HerculesControlCenterPage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai-command"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="AI Command Center" recoveryHref="/">
              <AiCommandCenterPage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai-workspace"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="AI Workspace" recoveryHref="/ai-command">
              <AiWorkspacePage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/memory"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="AI Workspace" recoveryHref="/ai-command">
              <AiWorkspacePage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/automation-engine"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="Universal Automation" recoveryHref="/automation">
              <AutomationCenterPage45 />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/workflows"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="Universal Automation" recoveryHref="/automation">
              <AutomationCenterPage45 />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/learning"
        element={
          <ProtectedRoute>
            <SelfLearningEnterprisePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/okr"
        element={
          <ProtectedRoute>
            <EnterpriseOkrPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/governance"
        element={
          <ProtectedRoute>
            <EnterpriseGovernancePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/demo/scenario"
        element={
          <ProtectedRoute>
            <DemoScenarioPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/pilot"
        element={
          <ProtectedRoute>
            <PilotDashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/pilot/production"
        element={
          <ProtectedRoute>
            <ProductionReadinessPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/pilot/onboard"
        element={
          <ProtectedRoute>
            <ExternalPilotOnboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/pilot/invite"
        element={
          <ProtectedRoute>
            <PilotInvitePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/pilot/execute"
        element={
          <ProtectedRoute>
            <PilotExecutionPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/invite/accept"
        element={<InviteAcceptPage />}
      />
      <Route
        path="/workspace"
        element={
          <ProtectedRoute>
            <WorkspaceHomePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/list"
        element={
          <ProtectedRoute>
            <WorkspacesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/dashboards"
        element={
          <ProtectedRoute>
            <DashboardsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/dashboards/:dashboardId"
        element={
          <ProtectedRoute>
            <DashboardsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/layout"
        element={
          <ProtectedRoute>
            <LayoutEditorPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/settings"
        element={
          <ProtectedRoute>
            <WorkspaceSettingsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/auto"
        element={
          <ProtectedRoute>
            <WorkspaceLandingGate landingId="auto">
              <AutoBusinessPage />
            </WorkspaceLandingGate>
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/auto/pilot"
        element={
          <ProtectedRoute>
            <AutomotiveLiveWorkflowPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/auto/:sub"
        element={
          <ProtectedRoute>
            <AutoBusinessPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/beauty"
        element={
          <ProtectedRoute>
            <BeautyBusinessPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/beauty/:sub"
        element={
          <ProtectedRoute>
            <BeautyBusinessPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/cafe"
        element={
          <ProtectedRoute>
            <WorkspaceLandingGate landingId="cafe">
              <CafeBusinessPage />
            </WorkspaceLandingGate>
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/cafe/:sub"
        element={
          <ProtectedRoute>
            <CafeBusinessPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/agro"
        element={
          <ProtectedRoute>
            <WorkspaceLandingGate landingId="agro">
              <AgroBusinessPage />
            </WorkspaceLandingGate>
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/agro/pilot"
        element={
          <ProtectedRoute>
            <AgricultureLiveWorkflowPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/agro/:sub"
        element={
          <ProtectedRoute>
            <AgroBusinessPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/legal"
        element={
          <ProtectedRoute>
            <WorkspaceLandingGate landingId="legal">
              <LawyerBusinessPage />
            </WorkspaceLandingGate>
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/legal/pilot"
        element={
          <ProtectedRoute>
            <LegalLiveWorkflowPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/legal/:sub"
        element={
          <ProtectedRoute>
            <LawyerBusinessPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/crypto"
        element={
          <ProtectedRoute>
            <WorkspaceLandingGate landingId="crypto">
              <CryptoOtcDeskPage />
            </WorkspaceLandingGate>
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/crypto/:sub"
        element={
          <ProtectedRoute>
            <CryptoOtcDeskPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/drone"
        element={
          <ProtectedRoute>
            <WorkspaceLandingGate landingId="drone">
              <DroneLiveWorkflowPage />
            </WorkspaceLandingGate>
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/drone/:sub"
        element={
          <ProtectedRoute>
            <DroneLiveWorkflowPage />
          </ProtectedRoute>
        }
      />
      {/* Sprint 42.8 — Universal Vertical Workspace Framework */}
      <Route
        path="/vertical/:verticalId"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="VerticalWorkspace" recoveryHref="/vertical/owner">
              <VerticalWorkspacePage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/vertical/:verticalId/:sectionId"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="VerticalWorkspaceSection" recoveryHref="/vertical/owner">
              <VerticalWorkspacePage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      {/* Sprint 42.9 — AI Tasks center */}
      <Route
        path="/ai-tasks"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="AiTasks" recoveryHref="/dashboard">
              <AiTasksPage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      {/* Sprint 40.3 — ACC-40-005 workspace → canonical hubs */}
      <Route path="/workspace/crm" element={<Navigate to="/crm" replace />} />
      <Route path="/workspace/erp" element={<Navigate to="/erp" replace />} />
      <Route path="/workspace/docs" element={<Navigate to="/documents" replace />} />
      <Route path="/workspace/documents" element={<Navigate to="/documents" replace />} />
      <Route path="/workspace/analytics" element={<Navigate to="/analytics" replace />} />
      <Route path="/workspace/reports" element={<Navigate to="/analytics" replace />} />
      <Route
        path="/workspace/:module"
        element={
          <ProtectedRoute>
            <WorkspaceModulePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/:module/:sub"
        element={
          <ProtectedRoute>
            <WorkspaceModulePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/portals/customer"
        element={
          <ProtectedRoute>
            <CustomerPortalPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/portals/employee"
        element={
          <ProtectedRoute>
            <EmployeePortalPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/portals/owner"
        element={
          <ProtectedRoute>
            <OwnerPortalPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/portals/mission-control"
        element={
          <ProtectedRoute>
            <Navigate to="/platform-builder/mission-control" replace />
          </ProtectedRoute>
        }
      />
      <Route
        path="/navigation"
        element={
          <ProtectedRoute>
            <NavigationDashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/command-center"
        element={
          <ProtectedRoute>
            <CommandCenterPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/command-runtime"
        element={
          <ProtectedRoute>
            <Suspense fallback={<LoadingScreen />}>
              <CommandRuntimeInspectorPage />
            </Suspense>
          </ProtectedRoute>
        }
      />
      <Route
        path="/workflow-runtime"
        element={
          <ProtectedRoute>
            <Suspense fallback={<LoadingScreen />}>
              <WorkflowRuntimeInspectorPage />
            </Suspense>
          </ProtectedRoute>
        }
      />
      <Route
        path="/automation"
        element={
          <ProtectedRoute>
            <Suspense fallback={<LoadingScreen />}>
              <AutomationCenterPage />
            </Suspense>
          </ProtectedRoute>
        }
      />
      <Route
        path="/automation-center"
        element={<Navigate to="/automation" replace />}
      />
      <Route
        path="/business-network"
        element={
          <ProtectedRoute>
            <Suspense fallback={<LoadingScreen />}>
              <BusinessNetworkPage />
            </Suspense>
          </ProtectedRoute>
        }
      />
      <Route
        path="/ebn"
        element={<Navigate to="/business-network" replace />}
      />
      <Route
        path="/digital-citizens"
        element={
          <ProtectedRoute>
            <Suspense fallback={<LoadingScreen />}>
              <DigitalCitizenPage />
            </Suspense>
          </ProtectedRoute>
        }
      />
      <Route path="/citizens" element={<Navigate to="/digital-citizens" replace />} />
      <Route
        path="/life-engine"
        element={
          <ProtectedRoute>
            <Suspense fallback={<LoadingScreen />}>
              <LifeEnginePage />
            </Suspense>
          </ProtectedRoute>
        }
      />
      <Route path="/life" element={<Navigate to="/life-engine" replace />} />
      <Route
        path="/assets"
        element={
          <ProtectedRoute>
            <Suspense fallback={<LoadingScreen />}>
              <AssetRuntimePage />
            </Suspense>
          </ProtectedRoute>
        }
      />
      <Route path="/asset-runtime" element={<Navigate to="/assets" replace />} />
      <Route
        path="/spatial"
        element={
          <ProtectedRoute>
            <Suspense fallback={<LoadingScreen />}>
              <SpatialRuntimePage />
            </Suspense>
          </ProtectedRoute>
        }
      />
      <Route path="/spatial-runtime" element={<Navigate to="/spatial" replace />} />
      <Route
        path="/city-visualization"
        element={
          <ProtectedRoute>
            <Suspense fallback={<LoadingScreen />}>
              <CityVisualizationPage />
            </Suspense>
          </ProtectedRoute>
        }
      />
      <Route path="/city-viz" element={<Navigate to="/city-visualization" replace />} />
      <Route
        path="/interactions"
        element={
          <ProtectedRoute>
            <Suspense fallback={<LoadingScreen />}>
              <InteractionRuntimePage />
            </Suspense>
          </ProtectedRoute>
        }
      />
      <Route path="/interaction-runtime" element={<Navigate to="/interactions" replace />} />
      <Route
        path="/intelligence"
        element={
          <ProtectedRoute>
            <Suspense fallback={<LoadingScreen />}>
              <IntelligenceRuntimePage />
            </Suspense>
          </ProtectedRoute>
        }
      />
      <Route path="/intelligence-runtime" element={<Navigate to="/intelligence" replace />} />
      <Route
        path="/orchestrator"
        element={
          <ProtectedRoute>
            <Suspense fallback={<LoadingScreen />}>
              <OrchestratorPage />
            </Suspense>
          </ProtectedRoute>
        }
      />
      <Route path="/orchestrator-runtime" element={<Navigate to="/orchestrator" replace />} />
      <Route
        path="/kernel"
        element={
          <ProtectedRoute>
            <Suspense fallback={<LoadingScreen />}>
              <KernelPage />
            </Suspense>
          </ProtectedRoute>
        }
      />
      <Route path="/enterprise-kernel" element={<Navigate to="/kernel" replace />} />
      <Route path="/kernel-runtime" element={<Navigate to="/kernel" replace />} />
      <Route
        path="/release"
        element={
          <ProtectedRoute>
            <ReleaseCandidatePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai-os"
        element={
          <ProtectedRoute>
            <AIOSPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/organization-brain"
        element={
          <ProtectedRoute>
            <OrganizationBrainPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/vertical-federation"
        element={
          <ProtectedRoute>
            <VerticalFederationPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder"
        element={
          <ProtectedRoute>
            <WorkspaceLandingGate landingId="platform">
              <PlatformBuilderDashboard />
            </WorkspaceLandingGate>
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/framework"
        element={
          <ProtectedRoute>
            <UniversalFrameworkPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/ai"
        element={
          <ProtectedRoute>
            <Navigate to="/platform-builder/builder-studio" replace />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/concierge"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="AI Concierge" recoveryHref="/dashboard?mode=executive">
              <ConciergeBuilderPage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/ai-team"
        element={
          <ProtectedRoute>
            <AITeamCenterPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/collaborative-ai"
        element={
          <ProtectedRoute>
            <CollaborativeAIPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/operations"
        element={
          <ProtectedRoute>
            <OperationsCenterPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/team-map"
        element={
          <ProtectedRoute>
            <TeamMapPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/visual-behavior"
        element={
          <ProtectedRoute>
            <VisualBehaviorPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/rendering"
        element={
          <ProtectedRoute>
            <RenderingEnginePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/themes"
        element={
          <ProtectedRoute>
            <ThemeEnginePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/assets"
        element={
          <ProtectedRoute>
            <AssetRegistryPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/simulation"
        element={
          <ProtectedRoute>
            <SimulationEnginePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/director"
        element={
          <ProtectedRoute>
            <DirectorEnginePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/story"
        element={
          <ProtectedRoute>
            <StoryEnginePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/intelligence"
        element={
          <ProtectedRoute>
            <IntelligenceEnginePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/experience"
        element={
          <ProtectedRoute>
            <ExperienceEnginePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/workspace-os"
        element={
          <ProtectedRoute>
            <WorkspaceOSPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/command-center"
        element={
          <ProtectedRoute>
            <CommandCenterOSPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/navigation-intelligence"
        element={
          <ProtectedRoute>
            <NavigationIntelligencePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/workflow-intelligence"
        element={
          <ProtectedRoute>
            <WorkflowIntelligencePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/digital-twin"
        element={
          <ProtectedRoute>
            <DigitalTwinPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/twin-intelligence"
        element={
          <ProtectedRoute>
            <TwinIntelligencePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/strategy"
        element={
          <ProtectedRoute>
            <StrategyEnginePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/mission-control"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="Mission Control" recoveryHref="/dashboard?mode=executive">
              <MissionControlPage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/business-ecosystem"
        element={
          <ProtectedRoute>
            <BusinessEcosystemPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/vertical"
        element={
          <ProtectedRoute>
            <VerticalBuilderPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/crm"
        element={
          <ProtectedRoute>
            <FrameBuilderPage builderId="crm" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/erp"
        element={
          <ProtectedRoute>
            <FrameBuilderPage builderId="erp" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/workflow"
        element={
          <ProtectedRoute>
            <FrameBuilderPage builderId="workflow" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/knowledge"
        element={
          <ProtectedRoute>
            <FrameBuilderPage builderId="knowledge" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/automation"
        element={
          <ProtectedRoute>
            <FrameBuilderPage builderId="automation" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/dashboard-builder"
        element={
          <ProtectedRoute>
            <FrameBuilderPage builderId="dashboard_builder" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/template"
        element={
          <ProtectedRoute>
            <FrameBuilderPage builderId="template" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/marketplace"
        element={
          <ProtectedRoute>
            <FrameBuilderPage builderId="marketplace" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/academy"
        element={
          <ProtectedRoute>
            <BuilderAcademyPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/god-mode"
        element={
          <ProtectedRoute>
            <GodModePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="Settings" recoveryHref="/dashboard">
              <SettingsPage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings/ai-mode"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="AI Mode Settings" recoveryHref="/settings">
              <ModeSettingsPage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings/ai"
        element={
          <ProtectedRoute>
            <RouteErrorBoundary zone="AI Mode Settings" recoveryHref="/settings">
              <ModeSettingsPage />
            </RouteErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/identity"
        element={
          <ProtectedRoute>
            <IdentityCenterPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/identity/users"
        element={
          <ProtectedRoute>
            <UsersPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/identity/organizations"
        element={
          <ProtectedRoute>
            <OrganizationsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/identity/roles"
        element={
          <ProtectedRoute>
            <RolesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/identity/permissions"
        element={
          <ProtectedRoute>
            <PermissionsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/identity/sessions"
        element={
          <ProtectedRoute>
            <SessionsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/identity/security"
        element={
          <ProtectedRoute>
            <SecurityCenterPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/identity/profile"
        element={
          <ProtectedRoute>
            <ProfileCenterPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/identity/activity"
        element={
          <ProtectedRoute>
            <ActivityCenterPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/identity/mfa"
        element={
          <ProtectedRoute>
            <MfaCenterPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<PlatformErrorPage kind="404" />} />
    </Routes>
    </Suspense>
  );
}
