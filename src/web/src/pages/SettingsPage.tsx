import { Link, useNavigate } from "react-router-dom";
import { FullLayout } from "@/layouts/FullLayout";
import { Button, Card, Select, Switch } from "@/ui";
import { useI18n, type Locale } from "@/i18n";
import { usePreferencesStore } from "@/preferences/preferencesStore";
import { useThemeStore, type ThemeMode } from "@/theme/themeStore";
import { resetFirstEntry, isFirstEntryComplete } from "@/onboarding/firstEntryStore";

/**
 * Settings — Sprint 32.3.1 adds personalization scaffold (structure for later sprints).
 * Theme / language / notifications reuse existing stores — no new engines.
 */
export function SettingsPage() {
  const navigate = useNavigate();
  const t = useI18n((s) => s.t);
  const setLocale = useI18n((s) => s.setLocale);
  const prefs = usePreferencesStore();
  const setMode = useThemeStore((s) => s.setMode);
  const firstEntryDone = isFirstEntryComplete();

  return (
    <FullLayout>
      <h1 className="mb-4 text-2xl font-semibold">{t("nav.settings")}</h1>
      <div className="grid max-w-3xl gap-4 lg:grid-cols-2">
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

        <Card title="Personalization (scaffold)">
          <p className="mb-3 eds-type-small text-[var(--eds-text-muted)]">
            Архитектурная основа для следующих спринт: темы, виджеты Dashboard, AI Team и Concierge.
            Полная функциональность будет подключена без смены архитектуры.
          </p>
          <ul className="eds-type-small space-y-2 text-[var(--eds-text-muted)]">
            <li>· Темы и оформление — themeStore / EDS tokens</li>
            <li>· Расположение виджетов — workspace personalizationEngine</li>
            <li>· Параметры Dashboard — /dashboard + dashboards page</li>
            <li>· Параметры AI Team — /platform-builder/ai-team</li>
            <li>· Параметры AI Concierge — /platform-builder/concierge</li>
            <li>· Персональные настройки — preferencesStore</li>
          </ul>
        </Card>

        <Card title="First entry">
          <p className="mb-3 eds-type-small text-[var(--eds-text-muted)]">
            Статус: {firstEntryDone ? "завершён" : "не завершён"}
          </p>
          <div className="flex flex-wrap gap-2">
            <Link to="/onboarding/first-entry">
              <Button size="sm" variant="secondary">
                Открыть мастер
              </Button>
            </Link>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => {
                resetFirstEntry();
                navigate("/onboarding/first-entry");
              }}
            >
              Пройти снова
            </Button>
          </div>
        </Card>
      </div>
    </FullLayout>
  );
}
