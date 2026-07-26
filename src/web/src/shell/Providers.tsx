import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { useThemeStore } from "@/theme/themeStore";
import { useAuthStore } from "@/auth/authStore";
import { LoadingScreen } from "./LoadingScreen";
import { NavigationProvider } from "../../navigation/components/NavigationProvider";
import { CommandCenterProvider } from "../../command-center/components/CommandCenterProvider";
import { WebCoreProvider } from "./WebCoreProvider";
import { telemetry } from "@/integrations/telemetry";
import { contextEngine } from "../../command-center/managers/contextEngine";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { detectActiveEcosystem } from "@/workspace-chrome/workspaceContext";
import { sectionKeyFromPath } from "@/ai-os-chrome/smartSuggestions";

const queryClient = new QueryClient();

function TelemetryRouterBridge() {
  const location = useLocation();
  useEffect(() => {
    void telemetry.pageView(location.pathname);
    const first = loadFirstEntry();
    const ws = useWorkspaceStore.getState().workspace;
    const user = useAuthStore.getState().user;
    const ecosystem = detectActiveEcosystem(location.pathname) || "platform";
    contextEngine.pushPage(location.pathname);
    contextEngine.patch({
      workspace: ws.project || first.workspaceId || "default",
      organization: first.companyName || ws.company,
      role: first.roleId || user?.roleId || ws.userContext || "user",
      department: ws.department || ecosystem,
      currentModule: sectionKeyFromPath(location.pathname),
      currentDashboard: location.pathname.includes("/dashboard") ? "command_center" : null,
    });
  }, [location.pathname]);
  return null;
}

export function Providers({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const apply = useThemeStore((s) => s.apply);
  const restoreSession = useAuthStore((s) => s.restoreSession);

  useEffect(() => {
    restoreSession();
    apply();
    void useAuthStore.getState().validateSession().finally(() => {
      void telemetry.sessionStart();
      setReady(true);
    });
  }, [apply, restoreSession]);

  if (!ready) return <LoadingScreen />;

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <CommandCenterProvider>
          <NavigationProvider>
            <WebCoreProvider>
              <TelemetryRouterBridge />
              {children}
            </WebCoreProvider>
          </NavigationProvider>
        </CommandCenterProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
