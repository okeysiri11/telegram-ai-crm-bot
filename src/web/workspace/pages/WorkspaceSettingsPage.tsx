import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Card, Checkbox, Select } from "@/ui";
import { personalizationEngine, workspaceSettings } from "../managers";
import { useState } from "react";
import { useI18n } from "@/i18n";
import { useThemeStore } from "@/theme/themeStore";
import { usePreferencesStore } from "@/preferences/preferencesStore";

export function WorkspaceSettingsPage() {
  const [prefs, setPrefs] = useState(personalizationEngine.get());
  const setLocale = useI18n((s) => s.setLocale);
  const setTheme = useThemeStore((s) => s.setMode);
  const updatePrefs = usePreferencesStore((s) => s.update);

  return (
    <WorkspaceLayout>
      <div className="mx-auto max-w-3xl space-y-4">
        <h1 className="eds-type-h1">Workspace Settings</h1>
        <p className="eds-type-small text-[var(--eds-text-muted)]">
          Sections: {workspaceSettings.sections.join(", ")}
        </p>
        <Card title="Personalization">
          <div className="space-y-3">
            <Select
              value={prefs.theme}
              onChange={(e) => {
                const theme = e.target.value as typeof prefs.theme;
                setPrefs(personalizationEngine.update({ theme }));
                setTheme(theme === "system" ? "system" : theme);
                updatePrefs({ theme: theme === "corporate" ? "light" : theme });
              }}
            >
              <option value="system">System</option>
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="corporate">Corporate</option>
            </Select>
            <Select
              value={prefs.language}
              onChange={(e) => {
                const language = e.target.value as typeof prefs.language;
                setPrefs(personalizationEngine.update({ language }));
                setLocale(language);
                updatePrefs({ language });
              }}
            >
              <option value="en">English</option>
              <option value="ru">Русский</option>
              <option value="uk">Українська</option>
            </Select>
            <Select
              value={prefs.defaultWorkspace}
              onChange={(e) => setPrefs(personalizationEngine.update({ defaultWorkspace: e.target.value, homePage: "/workspace" }))}
            >
              <option value="ws_personal">Personal</option>
              <option value="ws_team_ops">Team</option>
              <option value="ws_dept_finance">Department</option>
              <option value="ws_org">Organization</option>
              <option value="ws_project_web">Project</option>
            </Select>
            <label className="flex items-center gap-2 eds-type-small">
              <Checkbox
                checked={prefs.notificationPreferences.inApp}
                onChange={(e) =>
                  setPrefs(
                    personalizationEngine.update({
                      notificationPreferences: { ...prefs.notificationPreferences, inApp: e.target.checked },
                    }),
                  )
                }
              />
              In-app notifications
            </label>
          </div>
        </Card>
        <Card title="Defaults">
          <pre className="overflow-auto eds-type-caption">{JSON.stringify(workspaceSettings.defaults, null, 2)}</pre>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
