import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "@/shell/ProtectedRoute";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { EmptyLayout } from "@/layouts/EmptyLayout";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
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
        path="*"
        element={
          <EmptyLayout>
            <Navigate to="/" replace />
          </EmptyLayout>
        }
      />
    </Routes>
  );
}
