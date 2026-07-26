import { useNavigate } from "react-router-dom";
import { useI18n } from "@/i18n";
import { useAuthStore } from "@/auth/authStore";
import { useNotificationStore } from "@/notifications/notificationStore";
import { Avatar, Badge, Button, Input } from "@/ui";
import { Breadcrumbs } from "./Breadcrumbs";
import { useThemeStore } from "@/theme/themeStore";
import { useNavigationUi } from "../../navigation/components/NavigationProvider";
import { searchProvider } from "../../navigation/managers/searchProvider";
import { navigationHistory } from "../../navigation/managers/navigationHistory";
import { useState } from "react";
import { telemetry } from "@/integrations/telemetry";

export function TopNavigation({
  onMenuToggle,
}: {
  onMenuToggle?: () => void;
} = {}) {
  const t = useI18n((s) => s.t);
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const count = useNotificationStore((s) => s.items.filter((i) => !i.read).length);
  const mode = useThemeStore((s) => s.mode);
  const setMode = useThemeStore((s) => s.setMode);
  const { openPalette } = useNavigationUi();
  const [q, setQ] = useState("");

  return (
    <header className="border-b border-[var(--ew-border)] bg-[var(--ew-surface)]">
      <div className="flex flex-wrap items-center gap-3 px-4 py-3">
        {onMenuToggle ? (
          <Button size="sm" variant="secondary" className="md:hidden" onClick={onMenuToggle} aria-label="Open menu">
            Menu
          </Button>
        ) : null}
        <div className="min-w-48 flex-1">
          <Input
            placeholder={`${t("common.search")} · ⌘/Ctrl+K`}
            aria-label={t("common.search")}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onFocus={openPalette}
            onKeyDown={(e) => {
              if (e.key === "Enter" && q.trim()) {
                const hit = searchProvider.search(q)[0];
                if (hit) {
                  navigationHistory.push({ kind: "search", label: q, path: hit.path });
                  void telemetry.userActivity(`search:${hit.path}`);
                  navigate(hit.path);
                  setQ("");
                } else {
                  openPalette();
                }
              }
            }}
          />
        </div>
        <Button size="sm" variant="secondary" onClick={openPalette}>
          ⌘K
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => {
            void telemetry.userActivity("open_enterprise_city");
            navigate("/enterprise-city");
          }}
        >
          City
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => {
            void telemetry.userActivity("open_mission_control");
            navigate("/platform-builder/mission-control");
          }}
        >
          Mission Control
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => {
            void telemetry.userActivity("open_pilot_dashboard");
            navigate("/pilot");
          }}
        >
          Pilot
        </Button>
        <Badge tone="warning">{count} alerts</Badge>
        {user?.roleId ? <Badge>{user.roleId}</Badge> : null}
        <Button
          size="sm"
          variant="secondary"
          onClick={() => setMode(mode === "dark" ? "light" : "dark")}
        >
          Theme
        </Button>
        {user ? <Avatar name={user.name} /> : null}
        <Button size="sm" variant="ghost" onClick={() => navigate("/auth/logout")}>
          {t("auth.logout")}
        </Button>
      </div>
      <div className="px-4 pb-3">
        <Breadcrumbs />
      </div>
    </header>
  );
}
