import { Link, useLocation, useNavigate } from "react-router-dom";
import { useVerticalWorkspaceStore } from "@/vertical-workspace/verticalWorkspaceStore";
import { useMobileChromeStore } from "./mobileChromeStore";
import { isOwnerSystemContext, workspaceHomePath } from "./mobileWorkspace";

export function MobileBottomNav() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const setMoreOpen = useMobileChromeStore((s) => s.setMoreOpen);
  const setCreateOpen = useMobileChromeStore((s) => s.setCreateOpen);
  const moreOpen = useMobileChromeStore((s) => s.moreOpen);
  const createOpen = useMobileChromeStore((s) => s.createOpen);
  const verticalId = useVerticalWorkspaceStore((s) => s.verticalId);
  const workspaceHref = isOwnerSystemContext(verticalId) ? "/workspace" : workspaceHomePath(verticalId);

  const homeActive = pathname === "/dashboard";
  const workspaceActive = pathname === "/workspace" || pathname.startsWith("/workspace/") || pathname.startsWith("/vertical/");
  const notificationsActive = pathname === "/notifications";

  return (
    <nav className="ados-mobile-bottom" data-testid="mobile-bottom-nav" aria-label="Мобильная навигация">
      <Link to="/dashboard" className={homeActive ? "is-active" : undefined} data-testid="mobile-bottom-home">
        <span aria-hidden>⌂</span>
        Главная
      </Link>
      <button
        type="button"
        className={workspaceActive ? "is-active" : undefined}
        data-testid="mobile-bottom-workspace"
        onClick={() => navigate(workspaceHref)}
      >
        <span aria-hidden>▣</span>
        Workspace
      </button>
      <button
        type="button"
        aria-label="Создать"
        className={createOpen ? "is-active" : undefined}
        data-testid="mobile-bottom-create"
        onClick={() => setCreateOpen(true)}
      >
        <span className="ados-mobile-bottom__plus">＋</span>
      </button>
      <button
        type="button"
        className={notificationsActive ? "is-active" : undefined}
        data-testid="mobile-bottom-notifications"
        onClick={() => navigate("/notifications")}
      >
        <span aria-hidden>🔔</span>
        Уведомления
      </button>
      <button
        type="button"
        className={moreOpen ? "is-active" : undefined}
        data-testid="mobile-bottom-more"
        onClick={() => setMoreOpen(true)}
      >
        <span aria-hidden>☰</span>
        Ещё
      </button>
    </nav>
  );
}
