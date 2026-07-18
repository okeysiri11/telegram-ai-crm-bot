import { useNotificationStore } from '../../stores/notificationStore';
import { useAuthStore } from '../../stores/authStore';
import { useThemeStore } from '../../stores/themeStore';
import type { RealtimeStatus } from '../../services/realtime';
import { Badge } from '../ui/Card';

interface TopNavProps {
  realtimeStatus: RealtimeStatus;
  onToggleSidebar: () => void;
  onToggleNotifications: () => void;
  showNotifications: boolean;
}

export function TopNav({
  realtimeStatus,
  onToggleSidebar,
  onToggleNotifications,
  showNotifications,
}: TopNavProps) {
  const unread = useNotificationStore((s) => s.unreadCount);
  const logout = useAuthStore((s) => s.logout);
  const roles = useAuthStore((s) => s.roles);
  const actorId = useAuthStore((s) => s.actorTelegramId);
  const theme = useThemeStore((s) => s.theme);
  const setTheme = useThemeStore((s) => s.setTheme);

  const statusColor =
    realtimeStatus === 'connected'
      ? 'success'
      : realtimeStatus === 'connecting'
        ? 'warning'
        : 'danger';

  return (
    <header className="relative flex h-14 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-panel)] px-4">
      <div className="flex items-center gap-3">
        <button type="button" onClick={onToggleSidebar} className="rounded p-2 hover:bg-slate-100 dark:hover:bg-slate-800">
          ☰
        </button>
        <Badge variant={statusColor}>Live: {realtimeStatus}</Badge>
      </div>

      <div className="flex items-center gap-3">
        <select
          value={theme}
          onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'system')}
          className="rounded border border-[var(--color-border)] bg-transparent px-2 py-1 text-sm"
        >
          <option value="system">System</option>
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>

        <button
          type="button"
          onClick={onToggleNotifications}
          className="relative rounded p-2 hover:bg-slate-100 dark:hover:bg-slate-800"
        >
          🔔
          {unread > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] text-white">
              {unread}
            </span>
          )}
        </button>

        <div className="relative group">
          <button type="button" className="flex items-center gap-2 rounded-lg px-3 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-800">
            <span className="text-sm">{actorId || 'User'}</span>
            <Badge>{roles[0] || 'guest'}</Badge>
          </button>
          <div className="absolute right-0 z-50 hidden w-40 rounded-lg border border-[var(--color-border)] bg-[var(--color-panel)] py-1 shadow-lg group-hover:block">
            <button type="button" onClick={logout} className="block w-full px-4 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-800">
              Logout
            </button>
          </div>
        </div>
      </div>

      {showNotifications && <NotificationPanel />}
    </header>
  );
}

function NotificationPanel() {
  const items = useNotificationStore((s) => s.items);
  const markAllRead = useNotificationStore((s) => s.markAllRead);

  return (
    <div className="absolute right-4 top-14 z-50 max-h-80 w-96 overflow-y-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-panel)] shadow-xl">
      <div className="flex items-center justify-between border-b border-[var(--color-border)] px-4 py-2">
        <span className="font-semibold">Notifications</span>
        <button type="button" onClick={markAllRead} className="text-xs text-[var(--color-accent)]">
          Mark all read
        </button>
      </div>
      {items.length === 0 ? (
        <p className="p-4 text-sm text-[var(--color-muted)]">No notifications</p>
      ) : (
        items.slice(0, 20).map((n) => (
          <div key={n.id} className="border-b border-[var(--color-border)] px-4 py-2 text-sm">
            <div className="font-medium">{n.title}</div>
            <div className="text-xs text-[var(--color-muted)]">{n.message}</div>
          </div>
        ))
      )}
    </div>
  );
}
