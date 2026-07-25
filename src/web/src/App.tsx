import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "@/shell/ProtectedRoute";
import { DashboardPage } from "@/pages/DashboardPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { EmptyLayout } from "@/layouts/EmptyLayout";
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
  WorkspaceSettingsPage,
  WorkspacesPage,
} from "../workspace/pages";
import { NavigationDashboardPage } from "../navigation/pages";
import { CommandCenterPage } from "../command-center/pages";
import { ReleaseCandidatePage } from "../release/pages";
import { AIOSPage } from "../ai-os/pages";
import { OrganizationBrainPage } from "../organization-brain/pages";
import { VerticalFederationPage } from "../vertical-federation/pages";
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
            <Navigate to="/workspace" replace />
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
            <Navigate to="/workspace" replace />
          </EmptyLayout>
        }
      />
    </Routes>
  );
}
