import { useNavigate } from "react-router-dom";
import { useI18n } from "@/i18n";
import { useAuthStore } from "@/auth/authStore";
import { useNotificationStore } from "@/notifications/notificationStore";
import { Avatar, Badge, Button, Input } from "@/ui";
import { Breadcrumbs } from "./Breadcrumbs";
import { useThemeStore } from "@/theme/themeStore";

export function TopNavigation() {
  const t = useI18n((s) => s.t);
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const count = useNotificationStore((s) => s.items.filter((i) => !i.read).length);
  const mode = useThemeStore((s) => s.mode);
  const setMode = useThemeStore((s) => s.setMode);

  return (
    <header className="border-b border-[var(--ew-border)] bg-[var(--ew-surface)]">
      <div className="flex flex-wrap items-center gap-3 px-4 py-3">
        <div className="min-w-48 flex-1">
          <Input placeholder={t("common.search")} aria-label={t("common.search")} />
        </div>
        <Badge tone="warning">{count} alerts</Badge>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => setMode(mode === "dark" ? "light" : "dark")}
        >
          Theme
        </Button>
        {user ? <Avatar name={user.name} /> : null}
        <Button size="sm" variant="ghost" onClick={() => navigate("/auth/logout")}>{t("auth.logout")}</Button>
      </div>
      <div className="px-4 pb-3">
        <Breadcrumbs />
      </div>
    </header>
  );
}
