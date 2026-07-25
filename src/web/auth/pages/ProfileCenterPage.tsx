import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Button, Card, Checkbox, Input, Select } from "@/ui";
import { profileCenter } from "../managers";
import { useState } from "react";
import { usePreferencesStore } from "@/preferences/preferencesStore";
import { useThemeStore } from "@/theme/themeStore";
import { useI18n } from "@/i18n";
import { accessibilityManager } from "../../design-system/accessibility";

export function ProfileCenterPage() {
  const [profile, setProfile] = useState(profileCenter.get());
  const prefs = usePreferencesStore();
  const setTheme = useThemeStore((s) => s.setMode);
  const setLocale = useI18n((s) => s.setLocale);

  return (
    <DashboardLayout>
      <div className="mx-auto max-w-2xl space-y-4">
        <h1 className="eds-type-h1">Profile Center</h1>
        <Card title="Personal information">
          <div className="space-y-3">
            <Input value={profile.name} onChange={(e) => setProfile(profileCenter.update({ name: e.target.value }))} />
            <Input value={profile.avatar} placeholder="Avatar URL" onChange={(e) => setProfile(profileCenter.update({ avatar: e.target.value }))} />
            <Select
              value={profile.theme}
              onChange={(e) => {
                const theme = e.target.value as typeof profile.theme;
                setProfile(profileCenter.update({ theme }));
                if (theme !== "system") setTheme(theme);
                else setTheme("system");
                prefs.update({ theme: theme === "corporate" ? "light" : theme });
              }}
            >
              <option value="system">System</option>
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="corporate">Corporate</option>
            </Select>
            <Select
              value={profile.language}
              onChange={(e) => {
                const language = e.target.value as typeof profile.language;
                setProfile(profileCenter.update({ language }));
                setLocale(language);
                prefs.update({ language });
              }}
            >
              <option value="en">English</option>
              <option value="ru">Русский</option>
              <option value="uk">Українська</option>
            </Select>
            <Input value={profile.timeZone} onChange={(e) => { setProfile(profileCenter.update({ timeZone: e.target.value })); prefs.update({ timeZone: e.target.value }); }} />
            <label className="flex items-center gap-2 eds-type-small">
              <Checkbox checked={profile.notifications} onChange={(e) => { setProfile(profileCenter.update({ notifications: e.target.checked })); prefs.update({ notificationsEnabled: e.target.checked }); }} />
              Notifications
            </label>
            <label className="flex items-center gap-2 eds-type-small">
              <Checkbox
                checked={profile.accessibility.highContrast}
                onChange={(e) => {
                  const accessibility = { ...profile.accessibility, highContrast: e.target.checked };
                  setProfile(profileCenter.update({ accessibility }));
                  accessibilityManager.apply({
                    highContrast: accessibility.highContrast,
                    reduceMotion: accessibility.reduceMotion,
                  });
                  prefs.update({ accessibility });
                }}
              />
              High contrast
            </label>
            <label className="flex items-center gap-2 eds-type-small">
              <Checkbox
                checked={profile.accessibility.reduceMotion}
                onChange={(e) => {
                  const accessibility = { ...profile.accessibility, reduceMotion: e.target.checked };
                  setProfile(profileCenter.update({ accessibility }));
                  accessibilityManager.apply({
                    highContrast: accessibility.highContrast,
                    reduceMotion: accessibility.reduceMotion,
                  });
                  prefs.update({ accessibility });
                }}
              />
              Reduce motion
            </label>
            <label className="flex items-center gap-2 eds-type-small">
              <Checkbox checked={profile.dashboardPreferences.showKpis} onChange={(e) => setProfile(profileCenter.update({ dashboardPreferences: { ...profile.dashboardPreferences, showKpis: e.target.checked } }))} />
              Show KPIs on dashboard
            </label>
            <Button type="button" onClick={() => setProfile(profileCenter.get())}>Refresh</Button>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
}
