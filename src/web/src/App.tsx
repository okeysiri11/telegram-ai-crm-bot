import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "@/shell/ProtectedRoute";
import { DashboardPage } from "@/pages/DashboardPage";
import { PilotDashboardPage } from "@/pages/PilotDashboardPage";
import { ProductionReadinessPage } from "@/pages/ProductionReadinessPage";
import { ExternalPilotOnboardPage } from "@/pages/ExternalPilotOnboardPage";
import { PilotInvitePage } from "@/pages/PilotInvitePage";
import { InviteAcceptPage } from "@/pages/InviteAcceptPage";
import { PilotExecutionPage } from "@/pages/PilotExecutionPage";
import { FirstEntryPage } from "@/onboarding/FirstEntryPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { EnterpriseCityPage } from "@/enterprise-city";
import { WorkflowCenterPage } from "@/enterprise-workflow";
import { AIBuilderStudioPage } from "@/ai-builder-studio";
import { EnterpriseMarketplacePage } from "@/enterprise-marketplace";
import { EnterpriseTwinPage } from "@/enterprise-twin";
import { EnterpriseIntegrationHubPage } from "@/enterprise-integrations";
import { AIRuntimePage } from "@/ai-runtime";
import { EnterpriseDataFabricPage } from "@/enterprise-data-fabric";
import { PredictiveIntelligencePage } from "@/predictive-intelligence";
import { DemoScenarioPage } from "@/demo";
import { EmptyLayout } from "@/layouts/EmptyLayout";
import { EmptyState } from "@/ui";
import {
  AccessDeniedPage,
  AccountLockedPage,
  ActivityCenterPage,
  ChangePasswordPage,
  ForgotPasswordPage,
  IdentityCenterPage,
  LoginPage,
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
  AIBuilderPage,
  AITeamCenterPage,
  BuilderAcademyPage,
  CollaborativeAIPage,
  ConciergeBuilderPage,
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
  MissionControlPage,
  BusinessEcosystemPage,
} from "../platform-builder/pages";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/logout" element={<LogoutPage />} />
      <Route path="/auth/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/auth/reset-password" element={<ResetPasswordPage />} />
      <Route path="/auth/locked" element={<AccountLockedPage />} />
      <Route path="/auth/session-expired" element={<SessionExpiredPage />} />
      <Route path="/auth/access-denied" element={<AccessDeniedPage />} />
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
            <Navigate to="/dashboard" replace />
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
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/enterprise-city"
        element={
          <ProtectedRoute>
            <EnterpriseCityPage />
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
            <EnterpriseTwinPage />
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
            <AIBuilderPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/platform-builder/concierge"
        element={
          <ProtectedRoute>
            <ConciergeBuilderPage />
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
            <MissionControlPage />
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
            <SettingsPage />
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
      <Route
        path="*"
        element={
          <EmptyLayout>
            <div className="mx-auto max-w-lg p-8">
              <EmptyState
                title="Страница не найдена"
                description="Маршрут недоступен или устарел. Вернитесь в Workspace или Dashboard."
                actionLabel="Открыть Dashboard"
                actionTo="/dashboard"
                illustration="?"
              />
            </div>
          </EmptyLayout>
        }
      />
    </Routes>
  );
}
