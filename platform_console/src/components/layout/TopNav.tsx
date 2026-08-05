import type { WsStatus } from "../../hooks/useRuntimeSocket";

export function TopNav({
  wsStatus,
  systemStatus,
  onToggleSidebar,
}: {
  wsStatus: WsStatus;
  systemStatus?: string;
  onToggleSidebar: () => void;
}) {
  const live = wsStatus === "open";
  return (
    <header className="glass flex h-14 items-center justify-between border-b px-4">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onToggleSidebar}
          className="rounded-lg border border-[var(--border)] px-2 py-1 text-xs text-[var(--muted)] hover:bg-white/5"
        >
          Menu
        </button>
        <div className="text-sm text-[var(--muted)]">Enterprise Control Center</div>
      </div>
      <div className="flex items-center gap-4 text-xs">
        <span className="flex items-center gap-2">
          <span className={`status-dot ${live ? "status-ok" : "status-warn"}`} />
          WebSocket {wsStatus}
        </span>
        <span className="rounded-full border border-[var(--border)] px-3 py-1 text-[var(--ok)]">
          {systemStatus ?? "…"}
        </span>
      </div>
    </header>
  );
}
