import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useWorkspaceManager } from "./workspaceManagerStore";

/** Keeps Workspace tabs in sync with the router. */
export function useWorkspaceRouteSync() {
  const loc = useLocation();
  const hydrate = useWorkspaceManager((s) => s.hydrate);
  const syncRoute = useWorkspaceManager((s) => s.syncRoute);
  const hydrated = useWorkspaceManager((s) => s.hydrated);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (!hydrated) return;
    syncRoute(`${loc.pathname}${loc.search || ""}`);
  }, [loc.pathname, loc.search, hydrated, syncRoute]);
}

export function useWorkspaceNavigation() {
  const navigate = useNavigate();
  const openTab = useWorkspaceManager((s) => s.openTab);
  const activateTab = useWorkspaceManager((s) => s.activateTab);
  const closeTab = useWorkspaceManager((s) => s.closeTab);

  return {
    open: (path: string) => {
      const tab = openTab(path, { activate: true });
      navigate(tab.path);
      return tab;
    },
    activate: (id: string) => {
      const tab = activateTab(id);
      if (tab) navigate(tab.path);
      return tab;
    },
    close: (id: string) => {
      closeTab(id);
      const state = useWorkspaceManager.getState();
      const next = state.tabs.find((t) => t.id === state.activeTabId);
      navigate(next?.path || "/dashboard");
    },
  };
}
