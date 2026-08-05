import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "../components/layout/Sidebar";
import { TopNav } from "../components/layout/TopNav";
import { useLiveRuntime } from "../hooks/useLiveRuntime";
import { RuntimeContext } from "../context/RuntimeContext";

export function ControlShell() {
  const [collapsed, setCollapsed] = useState(false);
  const live = useLiveRuntime();

  return (
    <RuntimeContext.Provider value={live}>
      <div className="flex h-screen overflow-hidden">
        <Sidebar collapsed={collapsed} />
        <div className="flex flex-1 flex-col overflow-hidden">
          <TopNav
            wsStatus={live.socket.status}
            systemStatus={live.status.data?.systemStatus}
            onToggleSidebar={() => setCollapsed((c) => !c)}
          />
          <main className="flex-1 overflow-y-auto p-6">
            <Outlet />
          </main>
        </div>
      </div>
    </RuntimeContext.Provider>
  );
}
