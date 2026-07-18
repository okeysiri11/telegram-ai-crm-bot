import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AdminShell } from './layouts/AdminShell';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ManagementPage } from './pages/ManagementPage';
import { SettingsPage } from './pages/SettingsPage';
import { PluginsPage } from './pages/PluginsPage';
import { AiPage } from './pages/AiPage';
import { AiSkillsPage } from './pages/AiSkillsPage';
import { AiWorkflowsPage } from './pages/AiWorkflowsPage';
import { managementApi } from './services/management';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          element={
            <ProtectedRoute>
              <AdminShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route
            path="requests"
            element={
              <ManagementPage title="Requests" queryKey="requests" fetcher={managementApi.requests} />
            }
          />
          <Route
            path="managers"
            element={
              <ManagementPage title="Managers" queryKey="managers" fetcher={managementApi.managers} />
            }
          />
          <Route
            path="workflows"
            element={
              <ManagementPage title="Workflows" queryKey="workflows" fetcher={managementApi.workflows} />
            }
          />
          <Route
            path="configuration"
            element={
              <ProtectedRoute minRole="administrator">
                <ManagementPage
                  title="Configuration"
                  queryKey="configuration"
                  fetcher={managementApi.configuration}
                />
              </ProtectedRoute>
            }
          />
          <Route
            path="audit"
            element={<ManagementPage title="Audit" queryKey="audit" fetcher={() => managementApi.audit()} />}
          />
          <Route
            path="jobs"
            element={<ManagementPage title="Jobs" queryKey="jobs" fetcher={managementApi.jobs} />}
          />
          <Route
            path="integrations"
            element={
              <ManagementPage
                title="Integrations"
                queryKey="integrations"
                fetcher={managementApi.integrations}
              />
            }
          />
          <Route path="plugins" element={<PluginsPage />} />
          <Route path="ai" element={<AiPage />} />
          <Route path="ai/skills" element={<AiSkillsPage />} />
          <Route path="ai/workflows" element={<AiWorkflowsPage />} />
          <Route
            path="observability"
            element={
              <ManagementPage
                title="Observability"
                queryKey="observability"
                fetcher={managementApi.observability}
              />
            }
          />
          <Route
            path="system"
            element={<ManagementPage title="System" queryKey="system" fetcher={managementApi.system} />}
          />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
