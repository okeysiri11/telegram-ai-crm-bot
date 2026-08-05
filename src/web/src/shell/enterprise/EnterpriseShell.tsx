/**
 * Enterprise Shell boundary — Sprint 28.5.
 * Tracks module visits; lifecycle boot is owned by Providers.
 */

import { useEffect, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { enterpriseShellRuntime } from "./enterpriseShellRuntime";
import { useShellPreferences } from "./shellPreferencesStore";
import { shellModuleRegistry } from "./shellModuleRegistry";

export function EnterpriseShell({ children }: { children: ReactNode }) {
  const location = useLocation();
  const rememberModule = useShellPreferences((s) => s.rememberModule);
  const hydratePrefs = useShellPreferences((s) => s.hydrate);

  useEffect(() => {
    hydratePrefs();
  }, [hydratePrefs]);

  useEffect(() => {
    const path = location.pathname;
    const mod = shellModuleRegistry.list().find((m) => {
      const base = m.route.split("?")[0]!;
      return path === base || path.startsWith(base + "/");
    });
    if (mod) {
      rememberModule(mod.id);
      enterpriseShellRuntime.initializeModule(mod.id);
    }
  }, [location.pathname, rememberModule]);

  return <>{children}</>;
}
