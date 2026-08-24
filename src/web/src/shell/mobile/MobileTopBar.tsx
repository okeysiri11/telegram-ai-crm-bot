import { Link, useNavigate } from "react-router-dom";
import { Badge, Button } from "@/ui";
import { useNotificationStore } from "@/notifications/notificationStore";
import { liveBuildLabel } from "./liveBuildLabel";
import { useMobileChromeStore } from "./mobileChromeStore";

export function MobileTopBar({
  workspaceLabel,
  demo,
}: {
  workspaceLabel: string;
  demo?: boolean;
}) {
  const unread = useNotificationStore((s) => s.items.filter((i) => !i.read).length);
  const setDrawerOpen = useMobileChromeStore((s) => s.setDrawerOpen);
  const setMoreOpen = useMobileChromeStore((s) => s.setMoreOpen);
  const setSearchOpen = useMobileChromeStore((s) => s.setSearchOpen);
  const navigate = useNavigate();
  const live = liveBuildLabel();

  return (
    <header className="ados-mobile-top" data-testid="mobile-top-bar">
      <Button
        size="sm"
        variant="ghost"
        aria-label="Открыть меню рабочего пространства"
        data-testid="mobile-menu-toggle"
        onClick={() => setDrawerOpen(true)}
      >
        ☰
      </Button>
      <Link to="/dashboard" className="ados-mobile-top__brand font-bold" aria-label="ADOS">
        ADOS
      </Link>
      <p className="ados-mobile-top__ws" data-testid="mobile-workspace-name">
        {workspaceLabel}
      </p>
      {live ? (
        <span className="ados-mobile-live" data-testid="mobile-live-build">
          {live}
        </span>
      ) : null}
      {demo ? (
        <Badge tone="warning" data-testid="demo-badge">
          DEMO
        </Badge>
      ) : null}
      <Button
        size="sm"
        variant="ghost"
        aria-label="Поиск"
        data-testid="mobile-search-toggle"
        onClick={() => setSearchOpen(true)}
      >
        ⌕
      </Button>
      <Button
        size="sm"
        variant="ghost"
        aria-label="Уведомления"
        data-testid="mobile-notifications"
        onClick={() => navigate("/notifications")}
      >
        🔔{unread ? <span className="ml-0.5 text-xs">{unread}</span> : null}
      </Button>
      <Button
        size="sm"
        variant="ghost"
        aria-label="Ещё"
        data-testid="mobile-more-toggle"
        onClick={() => setMoreOpen(true)}
      >
        ⋮
      </Button>
    </header>
  );
}
