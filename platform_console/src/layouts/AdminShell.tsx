import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "../components/layout/Sidebar";
import { TopNav } from "../components/layout/TopNav";
import type { WsStatus } from "../hooks/useRuntimeSocket";
import { useRealtime } from "../hooks/useRealtime";

function mapRealtime(status: string): WsStatus {
  if (status === "connected" || status === "open") return "open";
  if (status === "connecting") return "connecting";
  if (status === "error") return "error";
  return "closed";
}

/** @deprecated Prefer ControlShell — kept for legacy management routes. */
export function AdminShell() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const realtimeStatus = useRealtime(true);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar collapsed={sidebarCollapsed} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopNav
          wsStatus={mapRealtime(String(realtimeStatus))}
          onToggleSidebar={() => setSidebarCollapsed((c) => !c)}
        />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
