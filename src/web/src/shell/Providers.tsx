import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { useEffect, useState } from "react";
import { useThemeStore } from "@/theme/themeStore";
import { useAuthStore } from "@/auth/authStore";
import { LoadingScreen } from "./LoadingScreen";
import { NavigationProvider } from "../../navigation/components/NavigationProvider";
import { CommandCenterProvider } from "../../command-center/components/CommandCenterProvider";

const queryClient = new QueryClient();

export function Providers({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const apply = useThemeStore((s) => s.apply);
  const restoreSession = useAuthStore((s) => s.restoreSession);

  useEffect(() => {
    restoreSession();
    apply();
    setReady(true);
  }, [apply, restoreSession]);

  if (!ready) return <LoadingScreen />;

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <CommandCenterProvider>
          <NavigationProvider>{children}</NavigationProvider>
        </CommandCenterProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
