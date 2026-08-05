import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ControlShell } from "./layouts/ControlShell";
import { DashboardPage } from "./pages/DashboardPage";
import { KernelPage } from "./pages/KernelPage";
import { ServicesPage } from "./pages/ServicesPage";
import { WorkflowsPage } from "./pages/WorkflowsPage";
import { AgentsPage } from "./pages/AgentsPage";
import { ProvidersPage } from "./pages/ProvidersPage";
import { KnowledgePage } from "./pages/KnowledgePage";
import { LogsPage } from "./pages/LogsPage";
import { EventsPage } from "./pages/EventsPage";
import { MarketplacePage } from "./pages/MarketplacePage";
import { OsSettingsPage } from "./pages/OsSettingsPage";
import { MemoryPage } from "./pages/MemoryPage";
import { TimelinePage } from "./pages/TimelinePage";
import { QueuePage } from "./pages/QueuePage";
import { TasksPage } from "./pages/TasksPage";
import { MetricsPage } from "./pages/MetricsPage";
import { ChatBridgePage } from "./pages/ChatBridgePage";
import { VoiceCenterPage } from "./pages/VoiceCenterPage";
import { McpGatewayPage } from "./pages/McpGatewayPage";
import { ExecutionPlannerPage } from "./pages/ExecutionPlannerPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<ControlShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="kernel" element={<KernelPage />} />
          <Route path="services" element={<ServicesPage />} />
          <Route path="workflows" element={<WorkflowsPage />} />
          <Route path="agents" element={<AgentsPage />} />
          <Route path="providers" element={<ProvidersPage />} />
          <Route path="chat-bridge" element={<ChatBridgePage />} />
          <Route path="voice" element={<VoiceCenterPage />} />
          <Route path="mcp" element={<McpGatewayPage />} />
          <Route path="execution" element={<ExecutionPlannerPage />} />
          <Route path="memory" element={<MemoryPage />} />
          <Route path="timeline" element={<TimelinePage />} />
          <Route path="tasks" element={<TasksPage />} />
          <Route path="queue" element={<QueuePage />} />
          <Route path="metrics" element={<MetricsPage />} />
          <Route path="knowledge" element={<KnowledgePage />} />
          <Route path="logs" element={<LogsPage />} />
          <Route path="events" element={<EventsPage />} />
          <Route path="marketplace" element={<MarketplacePage />} />
          <Route path="settings" element={<OsSettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
