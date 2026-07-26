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

const queryClient = new QueryClient();

function TelemetryRouterBridge() {
  const location = useLocation();
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
    void telemetry.sessionStart();
    setReady(true);
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
