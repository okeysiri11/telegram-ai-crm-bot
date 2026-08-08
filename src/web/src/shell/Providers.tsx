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
import { useIntegrationBoot } from "@/integration-hub";
import { EnterpriseShell } from "@/shell/enterprise/EnterpriseShell";
import { enterpriseShellRuntime } from "@/shell/enterprise/enterpriseShellRuntime";
import { InterfacePreferencesBoot } from "@/preferences/InterfacePreferencesBoot";

const queryClient = new QueryClient();

/**
 * Sprint 28.0 — Integration Hub bridge.
 * Shared context sync · session restore · universal search · event bus.
 * Replaces ad-hoc TelemetryRouterBridge contextEngine patching.
 * Sprint 28.5 — also boots Enterprise Shell Runtime (idempotent).
 */
function IntegrationHubBridge() {
  const location = useLocation();
  useIntegrationBoot();

  useEffect(() => {
    void enterpriseShellRuntime.startup();
  }, []);

  useEffect(() => {
    void telemetry.pageView(location.pathname);
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
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onScheme = () => {
      if (useThemeStore.getState().mode === "system") apply();
    };
    mq.addEventListener("change", onScheme);
    void useAuthStore.getState().validateSession().finally(() => {
      void telemetry.sessionStart();
      setReady(true);
    });
    return () => mq.removeEventListener("change", onScheme);
  }, [apply, restoreSession]);

  if (!ready) return <LoadingScreen />;

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <CommandCenterProvider>
          <NavigationProvider>
            <WebCoreProvider>
              <IntegrationHubBridge />
              <InterfacePreferencesBoot />
              <EnterpriseShell>{children}</EnterpriseShell>
            </WebCoreProvider>
          </NavigationProvider>
        </CommandCenterProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
