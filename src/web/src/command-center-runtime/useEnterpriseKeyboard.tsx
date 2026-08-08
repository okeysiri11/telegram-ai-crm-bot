import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useCommandCenterUi } from "../../command-center/components/CommandCenterProvider";
import { useWorkspaceManager } from "@/workspace-engine/workspaceManagerStore";
import { useShellLayoutStore, type DockSide } from "@/shell/enterprise/shellLayoutStore";
import { useAdaptiveShellStore } from "@/shell/enterprise/adaptiveShellStore";
import { logActivity } from "@/workspace-engine/activityJournal";

const PANEL_ORDER: DockSide[] = ["left", "right", "bottom"];

/**
 * Sprint 27.5 / 42.2 — keyboard-first workspace + adaptive shell shortcuts.
 * Ctrl+Shift+L/H/R/B/F — sidebar / header / activity / runtime / focus.
 */
export function useEnterpriseKeyboard() {
  const navigate = useNavigate();
  const { openPalette, openOmnibox, close, paletteOpen, omniboxOpen } = useCommandCenterUi();
  const tabs = useWorkspaceManager((s) => s.tabs);
  const activeTabId = useWorkspaceManager((s) => s.activeTabId);
  const activateTab = useWorkspaceManager((s) => s.activateTab);
  const closeTab = useWorkspaceManager((s) => s.closeTab);
  const reopenClosedTab = useWorkspaceManager((s) => s.reopenClosedTab);
  const toggleDock = useShellLayoutStore((s) => s.toggleDock);
  const docks = useShellLayoutStore((s) => s.docks);

  useEffect(() => {
    function typingTarget(el: EventTarget | null): boolean {
      if (!(el instanceof HTMLElement)) return false;
      const tag = el.tagName;
      return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable;
    }

    function onKey(e: KeyboardEvent) {
      if (typingTarget(e.target) && e.key !== "Escape") return;
      const meta = e.metaKey || e.ctrlKey;
      const key = e.key.toLowerCase();
      const adaptive = useAdaptiveShellStore.getState();

      // Sprint 42.2 — adaptive shell shortcuts
      if (meta && e.shiftKey && key === "l") {
        e.preventDefault();
        adaptive.toggleSidebar();
        logActivity({ kind: "system", title: "Toggle sidebar", detail: "Ctrl+Shift+L" });
        return;
      }
      if (meta && e.shiftKey && key === "h") {
        e.preventDefault();
        adaptive.toggleHeader();
        logActivity({ kind: "system", title: "Toggle header", detail: "Ctrl+Shift+H" });
        return;
      }
      if (meta && e.shiftKey && key === "r") {
        e.preventDefault();
        adaptive.cycleActivity();
        logActivity({ kind: "system", title: "Toggle activity", detail: "Ctrl+Shift+R" });
        return;
      }
      if (meta && e.shiftKey && key === "b") {
        e.preventDefault();
        adaptive.cycleRuntime();
        logActivity({ kind: "system", title: "Toggle runtime", detail: "Ctrl+Shift+B" });
        return;
      }
      if (meta && e.shiftKey && key === "f") {
        e.preventDefault();
        adaptive.toggleFocusMode();
        logActivity({ kind: "system", title: "Toggle focus mode", detail: "Ctrl+Shift+F" });
        return;
      }

      // Search workspace
      if (meta && key === "f" && !e.shiftKey) {
        e.preventDefault();
        navigate("/search");
        logActivity({ kind: "search", title: "Keyboard search", detail: "Ctrl/Cmd+F" });
        return;
      }

      // Close tab
      if (meta && key === "w") {
        e.preventDefault();
        if (activeTabId) {
          const next = closeTab(activeTabId);
          const tab = useWorkspaceManager.getState().tabs.find((t) => t.id === next);
          navigate(tab?.path || "/dashboard");
        }
        return;
      }

      // Reopen closed tab
      if (meta && e.shiftKey && key === "t") {
        e.preventDefault();
        const tab = reopenClosedTab();
        if (tab) navigate(tab.path);
        return;
      }

      // Switch tabs Alt+[ / Alt+]
      if (e.altKey && (key === "]" || key === "[")) {
        e.preventDefault();
        if (!tabs.length) return;
        const idx = tabs.findIndex((t) => t.id === activeTabId);
        const nextIdx =
          key === "]"
            ? (idx + 1) % tabs.length
            : (idx - 1 + tabs.length) % tabs.length;
        const tab = tabs[nextIdx];
        if (tab) {
          activateTab(tab.id);
          navigate(tab.path);
        }
        return;
      }

      // Next / previous panel Ctrl/Cmd+Alt+←/→ or Ctrl/Cmd+[ / ]
      if (meta && e.altKey && (key === "arrowright" || key === "arrowleft" || key === "]" || key === "[")) {
        e.preventDefault();
        const openSides = PANEL_ORDER.filter((s) => docks[s].open && !docks[s].collapsed);
        const focus = openSides[0] || "right";
        const i = PANEL_ORDER.indexOf(focus);
        const dir = key === "arrowright" || key === "]" ? 1 : -1;
        const next = PANEL_ORDER[(i + dir + PANEL_ORDER.length) % PANEL_ORDER.length]!;
        toggleDock(next);
        logActivity({ kind: "system", title: "Panel focus", detail: next });
        return;
      }

      // Navigate workspace home
      if (meta && key === "h" && !e.shiftKey) {
        e.preventDefault();
        navigate("/dashboard");
        return;
      }

      if (e.key === "Escape" && (paletteOpen || omniboxOpen)) {
        close();
      }
    }

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [
    navigate,
    openPalette,
    openOmnibox,
    close,
    paletteOpen,
    omniboxOpen,
    tabs,
    activeTabId,
    activateTab,
    closeTab,
    reopenClosedTab,
    toggleDock,
    docks,
  ]);
}
