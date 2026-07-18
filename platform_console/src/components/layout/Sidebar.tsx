import { Link, useLocation } from 'react-router-dom';
import { cn } from '../../utils/cn';
import { useAuthStore } from '../../stores/authStore';

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/requests', label: 'Requests', icon: '📋' },
  { path: '/managers', label: 'Managers', icon: '👥' },
  { path: '/workflows', label: 'Workflows', icon: '⚙️' },
  { path: '/configuration', label: 'Configuration', icon: '🔧', minRole: 'administrator' as const },
  { path: '/audit', label: 'Audit', icon: '📝' },
  { path: '/jobs', label: 'Jobs', icon: '⏱️' },
  { path: '/integrations', label: 'Integrations', icon: '🔌' },
  { path: '/plugins', label: 'Plugins', icon: '🧩', minRole: 'administrator' as const },
  { path: '/ai', label: 'AI', icon: '🤖' },
  { path: '/ai/skills', label: 'AI Skills', icon: '🎯' },
  { path: '/ai/workflows', label: 'AI Workflows', icon: '🔀' },
  { path: '/observability', label: 'Observability', icon: '📈' },
  { path: '/system', label: 'System', icon: '🖥️' },
  { path: '/settings', label: 'Settings', icon: '⚙️' },
];

export function Sidebar({ collapsed }: { collapsed: boolean }) {
  const location = useLocation();
  const hasRole = useAuthStore((s) => s.hasRole);

  return (
    <aside
      className={cn(
        'flex h-full flex-col border-r border-[var(--color-border)] bg-[var(--color-panel)] transition-all',
        collapsed ? 'w-16' : 'w-56',
      )}
    >
      <div className="flex h-14 items-center border-b border-[var(--color-border)] px-4">
        {!collapsed && <span className="font-bold text-[var(--color-accent)]">Platform Console</span>}
        {collapsed && <span className="text-xl">P</span>}
      </div>
      <nav className="flex-1 overflow-y-auto p-2">
        {NAV_ITEMS.filter((item) => !item.minRole || hasRole(item.minRole)).map((item) => {
          const active = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'mb-1 flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
                active
                  ? 'bg-[var(--color-accent)] text-white'
                  : 'text-[var(--color-muted)] hover:bg-slate-100 dark:hover:bg-slate-800',
              )}
            >
              <span>{item.icon}</span>
              {!collapsed && item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
