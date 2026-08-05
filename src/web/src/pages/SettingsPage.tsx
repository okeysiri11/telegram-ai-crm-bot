import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useEffect } from "react";
import { FullLayout } from "@/layouts/FullLayout";
import { Avatar, Badge, Button, Card, Select, Switch } from "@/ui";
import { useI18n, type Locale } from "@/i18n";
import { usePreferencesStore } from "@/preferences/preferencesStore";
import { useThemeStore, type ThemeMode } from "@/theme/themeStore";
import { resetFirstEntry, isFirstEntryComplete } from "@/onboarding/firstEntryStore";
import { rememberModuleRoute } from "@/modules/lastModuleStore";
import { useAuthStore } from "@/auth/authStore";
import { useWorkspaceManager } from "@/workspace-engine/workspaceManagerStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { webConfig } from "@/config/webConfig";

/**
 * Settings — Sprint 27.3: Theme · Language · Workspace · Notifications · Profile · Session
 * Sprint 27.7: embed mode for Desktop windows (?embed=1).
 */
export function SettingsPage() {
  const [params] = useSearchParams();
  const embed = params.get("embed") === "1";
  const navigate = useNavigate();
  const t = useI18n((s) => s.t);
  const setLocale = useI18n((s) => s.setLocale);
  const prefs = usePreferencesStore();
  const setMode = useThemeStore((s) => s.setMode);
  const mode = useThemeStore((s) => s.mode);
  const firstEntryDone = isFirstEntryComplete();
  const user = useAuthStore((s) => s.user);
  const accessExpiresAt = useAuthStore((s) => s.accessExpiresAt);
  const authMode = useAuthStore((s) => s.authMode);
  const logout = useAuthStore((s) => s.logout);
  const ws = useWorkspaceStore((s) => s.workspace);
  const setWorkspace = useWorkspaceStore((s) => s.setWorkspace);
  const activeWorkspaceId = useWorkspaceManager((s) => s.activeWorkspaceId);
  const setActiveWorkspace = useWorkspaceManager((s) => s.setActiveWorkspace);
  const tabs = useWorkspaceManager((s) => s.tabs);

  useEffect(() => {
    document.title = "Settings · ADOS Enterprise";
    rememberModuleRoute("/settings");
  }, []);

  const body = (
    <>
      <h1 className="mb-4 text-2xl font-semibold">{t("nav.settings")}</h1>
      <div className="grid max-w-5xl gap-4 lg:grid-cols-2">
        <Card title="Theme">
          <Select
            value={prefs.theme === "system" ? mode : prefs.theme}
            onChange={(e) => {
              const next = e.target.value as ThemeMode;
              prefs.update({ theme: next });
              setMode(next);
            }}
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="system">Auto (System)</option>
          </Select>
        </Card>

        <Card title="Language">
          <Select
            value={prefs.language}
            onChange={(e) => {
              const language = e.target.value as Locale;
              prefs.update({ language });
              setLocale(language);
            }}
          >
            <option value="en">English</option>
            <option value="ru">Русский</option>
            <option value="uk">Українська</option>
          </Select>
        </Card>

        <Card title="Workspace">
          <label className="eds-type-label mb-1 block">Active workspace</label>
          <Select
            value={activeWorkspaceId}
            onChange={(e) => setActiveWorkspace(e.target.value)}
          >
            <option value="ws_default">Default Workspace</option>
            <option value="ws_ops">Operations</option>
            <option value="ws_exec">Executive</option>
          </Select>
          <label className="eds-type-label mb-1 mt-3 block">Company / project</label>
          <Select
            value={ws.company}
            onChange={(e) => setWorkspace({ company: e.target.value })}
          >
            <option value="demo-corp">demo-corp</option>
            <option value="acme-ltd">acme-ltd</option>
          </Select>
          <p className="mt-2 eds-type-helper">{tabs.length} tab(s) will restore after refresh</p>
          {!embed ? (
            <div className="mt-3">
              <Link to="/desktop">
                <Button size="sm" variant="secondary">
                  Open Enterprise Desktop
                </Button>
              </Link>
            </div>
          ) : null}
        </Card>

        <Card title="Notifications">
          <Switch
            checked={prefs.notificationsEnabled}
            onChange={(v) => prefs.update({ notificationsEnabled: v })}
            label="In-app notifications"
          />
          <div className="mt-3">
            <Button size="sm" variant="secondary" onClick={() => navigate("/dashboard#notifications")}>
              Open Notification Center
            </Button>
          </div>
        </Card>

        <Card title="Profile">
          <div className="flex items-center gap-3">
            {user ? <Avatar name={user.name} /> : null}
            <div>
              <p className="font-medium">{user?.name || "—"}</p>
              <p className="eds-type-helper">{user?.email}</p>
              <Badge>{user?.roleId || "role"}</Badge>
            </div>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link to="/identity/profile">
              <Button size="sm">Open Profile Center</Button>
            </Link>
            <Link to="/identity/security">
              <Button size="sm" variant="secondary">
                Security
              </Button>
            </Link>
          </div>
        </Card>

        <Card title="Session">
          <ul className="space-y-2 eds-type-small">
            <li>
              Auth mode: <Badge>{authMode || "none"}</Badge>
            </li>
            <li>Tenant: {user?.tenantId || "—"}</li>
            <li>Expires: {accessExpiresAt || "session token"}</li>
            <li>Platform: {webConfig.version} · Sprint {webConfig.sprint}</li>
          </ul>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              End session
            </Button>
          </div>
        </Card>

        <Card title="First entry">
          <p className="mb-3 eds-type-small text-[var(--eds-text-muted)]">
            Status: {firstEntryDone ? "complete" : "incomplete"}
          </p>
          <div className="flex flex-wrap gap-2">
            <Link to="/onboarding/first-entry">
              <Button size="sm" variant="secondary">
                Open wizard
              </Button>
            </Link>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                resetFirstEntry();
                navigate("/onboarding/first-entry");
              }}
            >
              Reset
            </Button>
          </div>
        </Card>
      </div>
    </>
  );

  if (embed) {
    return <div className="edt-embed-root p-4">{body}</div>;
  }

  return <FullLayout>{body}</FullLayout>;
}
