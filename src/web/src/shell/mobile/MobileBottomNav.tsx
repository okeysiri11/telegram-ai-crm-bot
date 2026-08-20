import { Link, useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import { QuickCreatePanel } from "@/owner-experience";
import { useAdaptiveShellStore } from "@/shell/enterprise/adaptiveShellStore";
import { useMobileChromeStore } from "./mobileChromeStore";

export function MobileBottomNav({ workspaceHome }: { workspaceHome: string }) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const setMoreOpen = useMobileChromeStore((s) => s.setMoreOpen);
  const setActivityMode = useAdaptiveShellStore((s) => s.setActivityMode);
  const [createOpen, setCreateOpen] = useState(false);

  return (
    <>
      <nav className="ados-mobile-bottom" data-testid="mobile-bottom-nav" aria-label="Мобильная навигация">
        <Link to="/dashboard" className={pathname === "/dashboard" ? "is-active" : undefined}>
          <span aria-hidden>⌂</span>
          Главная
        </Link>
        <button
          type="button"
          className={pathname.startsWith("/workspace") || pathname.startsWith("/vertical") ? "is-active" : undefined}
          onClick={() => navigate(workspaceHome)}
        >
          <span aria-hidden>▣</span>
          Workspace
        </button>
        <button type="button" aria-label="Создать" onClick={() => setCreateOpen(true)}>
          <span className="ados-mobile-bottom__plus">＋</span>
        </button>
        <button type="button" onClick={() => setActivityMode("expanded")}>
          <span aria-hidden>🔔</span>
          Уведомления
        </button>
        <button type="button" data-testid="mobile-bottom-more" onClick={() => setMoreOpen(true)}>
          <span aria-hidden>☰</span>
          Ещё
        </button>
      </nav>
      <QuickCreatePanel open={createOpen} onClose={() => setCreateOpen(false)} />
    </>
  );
}
