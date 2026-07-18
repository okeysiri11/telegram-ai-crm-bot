import { useThemeStore } from '../stores/themeStore';
import { useLayoutStore } from '../stores/layoutStore';
import { Card } from '../components/ui/Card';

export function SettingsPage() {
  const theme = useThemeStore((s) => s.theme);
  const language = useThemeStore((s) => s.language);
  const timezone = useThemeStore((s) => s.timezone);
  const setTheme = useThemeStore((s) => s.setTheme);
  const setLanguage = useThemeStore((s) => s.setLanguage);
  const setTimezone = useThemeStore((s) => s.setTimezone);
  const resetLayout = useLayoutStore((s) => s.resetLayout);

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <Card title="Appearance">
        <label className="block text-sm">
          Theme
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'system')}
            className="mt-1 w-full rounded border border-[var(--color-border)] bg-transparent px-3 py-2"
          >
            <option value="system">System</option>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </label>
      </Card>

      <Card title="Regional">
        <div className="space-y-4">
          <label className="block text-sm">
            Language
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="mt-1 w-full rounded border border-[var(--color-border)] bg-transparent px-3 py-2"
            >
              <option value="en">English</option>
              <option value="ru">Russian</option>
            </select>
          </label>
          <label className="block text-sm">
            Timezone
            <input
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="mt-1 w-full rounded border border-[var(--color-border)] bg-transparent px-3 py-2"
            />
          </label>
        </div>
      </Card>

      <Card title="Dashboard">
        <p className="mb-3 text-sm text-[var(--color-muted)]">
          Reset widget layout to the default configuration.
        </p>
        <button
          type="button"
          onClick={resetLayout}
          className="rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm"
        >
          Reset dashboard layout
        </button>
      </Card>
    </div>
  );
}
