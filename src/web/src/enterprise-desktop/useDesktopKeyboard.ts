/**
 * Desktop keyboard — Sprint 27.7 / 28.4.
 * Ctrl+Tab · Ctrl+W · Ctrl+N · Ctrl+D · Ctrl+Space · Ctrl+Shift+P · Alt+Tab · Esc
 */

import { useEffect } from "react";
import { useDesktopStore } from "./desktopStore";
import { useCommandCenterUi } from "../../command-center/components/CommandCenterProvider";
import { commandRuntime } from "@/runtime/commandRuntime";

function isTyping(el: EventTarget | null): boolean {
  if (!(el instanceof HTMLElement)) return false;
  const tag = el.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable;
}

export function useDesktopKeyboard() {
  const cycleWindows = useDesktopStore((s) => s.cycleWindows);
  const setLauncherOpen = useDesktopStore((s) => s.setLauncherOpen);
  const launcherOpen = useDesktopStore((s) => s.launcherOpen);
  const closeWindow = useDesktopStore((s) => s.closeWindow);
  const focusedId = useDesktopStore((s) => s.focusedId);
  const reopenClosed = useDesktopStore((s) => s.reopenClosed);
  const openApp = useDesktopStore((s) => s.openApp);
  const windows = useDesktopStore((s) => s.windows);
  const duplicateTab = useDesktopStore((s) => s.duplicateTab);
  const toggleMaximize = useDesktopStore((s) => s.toggleMaximize);
  const minimizeWindow = useDesktopStore((s) => s.minimizeWindow);
  const snapWindow = useDesktopStore((s) => s.snapWindow);
  const setInspectorOpen = useDesktopStore((s) => s.setInspectorOpen);
  const inspectorOpen = useDesktopStore((s) => s.inspectorOpen);
  const setSnapPreview = useDesktopStore((s) => s.setSnapPreview);
  const { openPalette } = useCommandCenterUi();

  useEffect(() => {
    commandRuntime.setSurface("desktop");
    commandRuntime.startup();

    function onKey(e: KeyboardEvent) {
      if (isTyping(e.target) && e.key !== "Escape") return;
      const meta = e.metaKey || e.ctrlKey;
      const key = e.key.toLowerCase();

      if ((e.altKey || (meta && key === "tab")) && key === "tab") {
        e.preventDefault();
        cycleWindows(e.shiftKey ? -1 : 1);
        return;
      }

      if (meta && e.code === "Space") {
        e.preventDefault();
        setLauncherOpen(!launcherOpen);
        return;
      }

      if (e.key === "Escape") {
        setSnapPreview(null);
        if (launcherOpen) {
          setLauncherOpen(false);
          return;
        }
        if (inspectorOpen) {
          setInspectorOpen(false);
          return;
        }
      }

      if (meta && key === "w") {
        e.preventDefault();
        commandRuntime.executeSync("close_focused_window");
        return;
      }

      if (meta && key === "n") {
        e.preventDefault();
        const focused = windows.find((w) => w.id === focusedId);
        if (focused) openApp(focused.path, { forceNew: true, exactPath: true });
        else openApp("dashboard", { forceNew: true });
        return;
      }

      if (meta && key === "d") {
        e.preventDefault();
        const focused = windows.find((w) => w.id === focusedId);
        if (focused?.activeTabId) duplicateTab(focused.id, focused.activeTabId);
        return;
      }

      if (meta && e.shiftKey && key === "p") {
        e.preventDefault();
        openPalette();
        return;
      }

      if (meta && e.shiftKey && key === "t") {
        e.preventDefault();
        reopenClosed();
        return;
      }

      if (meta && e.shiftKey && key === "m" && focusedId) {
        e.preventDefault();
        commandRuntime.executeSync("maximize_focused_window");
        return;
      }

      if (meta && !e.shiftKey && key === "m" && focusedId) {
        e.preventDefault();
        commandRuntime.executeSync("minimize_focused_window");
        return;
      }

      if (meta && e.shiftKey && e.key === "ArrowLeft" && focusedId) {
        e.preventDefault();
        snapWindow(focusedId, "left");
        return;
      }

      if (meta && e.shiftKey && e.key === "ArrowRight" && focusedId) {
        e.preventDefault();
        snapWindow(focusedId, "right");
        return;
      }

      if (meta && e.shiftKey && key === "i") {
        e.preventDefault();
        setInspectorOpen(!inspectorOpen);
        return;
      }

      if (meta && key === "z" && !e.shiftKey) {
        e.preventDefault();
        commandRuntime.executeSync("sys_undo");
        return;
      }

      if (meta && e.shiftKey && key === "z") {
        e.preventDefault();
        commandRuntime.executeSync("sys_redo");
        return;
      }

      if (meta && key === "k") {
        e.preventDefault();
        openPalette();
      }
    }

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [
    cycleWindows,
    setLauncherOpen,
    launcherOpen,
    closeWindow,
    focusedId,
    reopenClosed,
    openApp,
    windows,
    duplicateTab,
    toggleMaximize,
    minimizeWindow,
    snapWindow,
    setInspectorOpen,
    inspectorOpen,
    setSnapPreview,
    openPalette,
  ]);
}
