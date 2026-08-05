import { Navigate, Route, Routes } from "react-router-dom";
import { lazy, Suspense } from "react";
import { ProtectedRoute } from "@/shell/ProtectedRoute";
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
import { PilotDashboardPage } from "@/pages/PilotDashboardPage";
import { ProductionReadinessPage } from "@/pages/ProductionReadinessPage";
import { ExternalPilotOnboardPage } from "@/pages/ExternalPilotOnboardPage";
import { PilotInvitePage } from "@/pages/PilotInvitePage";
import { InviteAcceptPage } from "@/pages/InviteAcceptPage";
import { PilotExecutionPage } from "@/pages/PilotExecutionPage";
import { FirstEntryPage } from "@/onboarding/FirstEntryPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { DemoScenarioPage } from "@/demo";
import { ModulePageById, SearchWorkspacePage } from "@/modules";
import { useLastModuleStore } from "@/modules/lastModuleStore";
import { DesktopShell } from "@/enterprise-desktop";

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
    roleId = localStorage.getItem("ewp_role_switcher_v1") || "employee";
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
import { BeautyLiveWorkflowPage } from "../workspace/beauty/BeautyLiveWorkflowPage";
import { CafeLiveWorkflowPage } from "../workspace/cafe/CafeLiveWorkflowPage";
import { AgricultureLiveWorkflowPage } from "../workspace/agriculture/AgricultureLiveWorkflowPage";
import { LegalLiveWorkflowPage } from "../workspace/legal/LegalLiveWorkflowPage";
import { BidexLiveWorkflowPage } from "../workspace/crypto/BidexLiveWorkflowPage";
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
              <OwnerDashboardPage />
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
              <AIAgentCenterPage />
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
            <AutomotiveLiveWorkflowPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/auto/:sub"
        element={
          <ProtectedRoute>
            <AutomotiveLiveWorkflowPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/beauty"
        element={
          <ProtectedRoute>
            <BeautyLiveWorkflowPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/beauty/:sub"
        element={
          <ProtectedRoute>
            <BeautyLiveWorkflowPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/cafe"
        element={
          <ProtectedRoute>
            <CafeLiveWorkflowPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/cafe/:sub"
        element={
          <ProtectedRoute>
            <CafeLiveWorkflowPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/agro"
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
            <AgricultureLiveWorkflowPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/legal"
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
            <LegalLiveWorkflowPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/crypto"
        element={
          <ProtectedRoute>
            <BidexLiveWorkflowPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/crypto/:sub"
        element={
          <ProtectedRoute>
            <BidexLiveWorkflowPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace/drone"
        element={
          <ProtectedRoute>
            <DroneLiveWorkflowPage />
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
            <PlatformBuilderDashboard />
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
