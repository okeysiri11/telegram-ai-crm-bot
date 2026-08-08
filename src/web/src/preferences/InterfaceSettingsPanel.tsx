/**
 * Sprint 41.2 — Interface Settings panel (density, font, menu, view mode, theme, language, docks).
 */

import { Card, Select, Switch } from "@/ui";
import { useI18n, type Locale } from "@/i18n";
import {
  usePreferencesStore,
  type DensityMode,
  type FontScale,
  type MenuWidth,
} from "@/preferences/preferencesStore";
import { useThemeStore, type ThemeMode } from "@/theme/themeStore";
import { useViewModeStore, VIEW_MODE_OPTIONS, type ViewModeId } from "@/ux-revolution";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { useShellLayoutStore } from "@/shell/enterprise";
import { ModuleHelpIcon } from "@/help/ModuleHelpIcon";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { ORG_SELECTOR_OPTIONS } from "@/navigation/enterpriseRuNav";
import { useToolbarStore } from "@/navigation/toolbarStore";
import { useWorkspaceTabChromeStore } from "@/workspace-engine/workspaceTabChromeStore";

export function InterfaceSettingsPanel() {
  const t = useI18n((s) => s.t);
  const setLocale = useI18n((s) => s.setLocale);
  const locale = useI18n((s) => s.locale);
  const prefs = usePreferencesStore();
  const setMode = useThemeStore((s) => s.setMode);
  const themeMode = useThemeStore((s) => s.mode);
  const viewMode = useViewModeStore((s) => s.viewMode);
  const setViewMode = useViewModeStore((s) => s.setViewMode);
  const setRole = useRoleSwitcher((s) => s.setRole);
  const right = useShellLayoutStore((s) => s.docks.right);
  const setDock = useShellLayoutStore((s) => s.setDock);
  const organizationId = useOrgSelector((s) => s.organizationId);
  const setOrganization = useOrgSelector((s) => s.setOrganization);
  const toolbarCollapsed = useToolbarStore((s) => s.collapsed);
  const setToolbarCollapsed = useToolbarStore((s) => s.setCollapsed);
  const tabChromeEnabled = useWorkspaceTabChromeStore((s) => s.enabled);
  const setTabChromeEnabled = useWorkspaceTabChromeStore((s) => s.setEnabled);

  function syncViewMode(next: ViewModeId) {
    setViewMode(next);
    if (next === "platform_owner") setRole("owner");
    else if (next === "company_admin") setRole("administrator");
    else if (next === "manager") setRole("manager");
    else if (next === "client") setRole("client");
    else setRole("administrator");
  }

  return (
    <div className="grid max-w-5xl gap-4 lg:grid-cols-2" data-testid="interface-settings">
      <div className="lg:col-span-2 flex items-center gap-2">
        <h2 className="eds-type-h2">{t("iface.title")}</h2>
        <ModuleHelpIcon pathname="/settings" />
      </div>

      <Card title={t("iface.density")}>
        <Select
          value={prefs.density}
          onChange={(e) => prefs.update({ density: e.target.value as DensityMode })}
          aria-label={t("iface.density")}
        >
          <option value="compact">{t("iface.density.compact")}</option>
          <option value="standard">{t("iface.density.standard")}</option>
          <option value="comfortable">{t("iface.density.comfortable")}</option>
        </Select>
      </Card>

      <Card title={t("iface.fontScale")}>
        <Select
          value={String(prefs.fontScale)}
          onChange={(e) => prefs.update({ fontScale: Number(e.target.value) as FontScale })}
          aria-label={t("iface.fontScale")}
        >
          {[80, 90, 100, 110, 120].map((n) => (
            <option key={n} value={n}>
              {n}%
            </option>
          ))}
        </Select>
      </Card>

      <Card title={t("iface.menuWidth")}>
        <Select
          value={prefs.menuWidth}
          onChange={(e) => prefs.update({ menuWidth: e.target.value as MenuWidth })}
          aria-label={t("iface.menuWidth")}
        >
          <option value="compact">{t("iface.menu.compact")}</option>
          <option value="standard">{t("iface.menu.standard")}</option>
          <option value="wide">{t("iface.menu.wide")}</option>
        </Select>
      </Card>

      <Card title={t("iface.rightPanel")}>
        <div className="space-y-2">
          <Switch
            checked={right.pinned}
            onChange={(v) => setDock("right", { pinned: v, autoHide: v ? false : right.autoHide })}
            label={t("iface.panel.pin")}
          />
          <Switch
            checked={right.autoHide}
            onChange={(v) => setDock("right", { autoHide: v, pinned: v ? false : right.pinned })}
            label={t("iface.panel.autoHide")}
          />
        </div>
        <p className="mt-2 eds-type-helper">{t("iface.panel.hint")}</p>
      </Card>

      <Card title={t("org.switcher")}>
        <Select
          value={organizationId}
          onChange={(e) => setOrganization(e.target.value)}
          aria-label={t("org.switcher")}
          data-testid="settings-company"
        >
          {ORG_SELECTOR_OPTIONS.map((o) => (
            <option key={o.id} value={o.id}>
              {o.label}
            </option>
          ))}
        </Select>
        <p className="mt-2 eds-type-helper">{t("iface.workspace.hint")}</p>
      </Card>

      <Card title={t("viewMode.label")}>
        <Select
          value={viewMode}
          onChange={(e) => syncViewMode(e.target.value as ViewModeId)}
          data-testid="view-mode-settings"
        >
          {VIEW_MODE_OPTIONS.map((o) => (
            <option key={o.id} value={o.id}>
              {locale === "en" ? o.labelEn : o.labelRu}
            </option>
          ))}
        </Select>
        <p className="mt-2 eds-type-helper">{t("viewMode.hint")}</p>
      </Card>

      {viewMode === "developer" ? (
        <Card title={t("devTabs.title")}>
          <div data-testid="dev-workspace-tabs-toggle">
            <Switch
              checked={tabChromeEnabled}
              onChange={(v) => setTabChromeEnabled(v)}
              label={t("devTabs.toggle")}
            />
          </div>
          <p className="mt-2 eds-type-helper">{t("devTabs.hint")}</p>
        </Card>
      ) : null}

      <Card title={t("toolbar.label")}>
        <Switch
          checked={toolbarCollapsed}
          onChange={(v) => setToolbarCollapsed(v)}
          label={t("toolbar.collapse")}
        />
        <p className="mt-2 eds-type-helper">{t("toolbar.settingsHint")}</p>
      </Card>

      <Card title={t("nav.theme")}>
        <Select
          value={prefs.theme === "system" ? themeMode : prefs.theme}
          onChange={(e) => {
            const next = e.target.value as ThemeMode;
            prefs.update({ theme: next });
            setMode(next);
          }}
        >
          <option value="light">{t("iface.theme.light")}</option>
          <option value="dark">{t("iface.theme.dark")}</option>
          <option value="system">{t("iface.theme.system")}</option>
        </Select>
      </Card>

      <Card title={t("nav.language")}>
        <Select
          value={prefs.language}
          onChange={(e) => {
            const language = e.target.value as Locale;
            prefs.update({ language });
            setLocale(language);
          }}
        >
          <option value="ru">Русский</option>
          <option value="en">English</option>
          <option value="uk">Українська</option>
        </Select>
      </Card>

      <Card title={t("iface.a11y")}>
        <div className="space-y-2">
          <Switch
            checked={prefs.accessibility.reduceMotion}
            onChange={(v) =>
              prefs.update({ accessibility: { ...prefs.accessibility, reduceMotion: v } })
            }
            label={t("iface.a11y.reduceMotion")}
          />
          <Switch
            checked={prefs.accessibility.highContrast}
            onChange={(v) =>
              prefs.update({ accessibility: { ...prefs.accessibility, highContrast: v } })
            }
            label={t("iface.a11y.highContrast")}
          />
        </div>
      </Card>
    </div>
  );
}
