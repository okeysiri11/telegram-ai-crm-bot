import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/layout/Sidebar';
import { TopNav } from '../components/layout/TopNav';
import { Breadcrumbs } from '../components/layout/Breadcrumbs';
import { useRealtime } from '../hooks/useRealtime';
import { useAuthRefresh } from '../hooks/useAuth';

export function AdminShell() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const realtimeStatus = useRealtime(true);
  useAuthRefresh();

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar collapsed={sidebarCollapsed} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopNav
          realtimeStatus={realtimeStatus}
          onToggleSidebar={() => setSidebarCollapsed((c) => !c)}
          onToggleNotifications={() => setShowNotifications((s) => !s)}
          showNotifications={showNotifications}
        />
        <main className="flex-1 overflow-y-auto p-6">
          <Breadcrumbs />
          <Outlet />
        </main>
      </div>
    </div>
  );
}
