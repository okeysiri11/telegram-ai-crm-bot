import { FullLayout } from "@/layouts/FullLayout";
import { Card, Select, Switch } from "@/ui";
import { useI18n, type Locale } from "@/i18n";
import { usePreferencesStore } from "@/preferences/preferencesStore";
import { useThemeStore, type ThemeMode } from "@/theme/themeStore";

export function SettingsPage() {
  const t = useI18n((s) => s.t);
  const setLocale = useI18n((s) => s.setLocale);
  const prefs = usePreferencesStore();
  const setMode = useThemeStore((s) => s.setMode);

  return (
    <FullLayout>
      <h1 className="mb-4 text-2xl font-semibold">{t("nav.settings")}</h1>
      <div className="grid max-w-2xl gap-4">
        <Card title="Theme">
          <Select
            value={prefs.theme}
            onChange={(e) => {
              const mode = e.target.value as ThemeMode;
              prefs.update({ theme: mode });
              setMode(mode);
            }}
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="system">System</option>
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
        <Card title="Notifications">
          <Switch
            checked={prefs.notificationsEnabled}
            onChange={(v) => prefs.update({ notificationsEnabled: v })}
            label="In-app notifications"
          />
        </Card>
      </div>
    </FullLayout>
  );
}
