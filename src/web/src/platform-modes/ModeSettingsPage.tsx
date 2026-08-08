/**
 * Epic 45.1 — Настройки AI / Настройки режима.
 */

import { useEffect } from "react";
import { Link } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Card, Switch } from "@/ui";
import { ModeIndicator, ModeSwitch } from "./ModeSwitch";
import { useModeStore } from "./modeStore";

type ToggleKey =
  | "remember_last_mode"
  | "start_in_human"
  | "start_in_ai"
  | "start_voice_after_login"
  | "require_confirmation"
  | "show_execution_plan"
  | "speak_answers"
  | "show_agents"
  | "show_cost"
  | "show_duration";

const TOGGLES: { key: ToggleKey; label: string }[] = [
  { key: "remember_last_mode", label: "Запоминать последний режим" },
  { key: "start_in_human", label: "Запускать в Human Mode" },
  { key: "start_in_ai", label: "Запускать сразу в AI" },
  { key: "start_voice_after_login", label: "Запускать Voice после входа" },
  { key: "require_confirmation", label: "Требовать подтверждение действий" },
  { key: "show_execution_plan", label: "Показывать план выполнения" },
  { key: "speak_answers", label: "Озвучивать ответы" },
  { key: "show_agents", label: "Показывать работающих агентов" },
  { key: "show_cost", label: "Показывать стоимость выполнения" },
  { key: "show_duration", label: "Показывать время выполнения" },
];

export function ModeSettingsPage() {
  const settings = useModeStore((s) => s.settings);
  const updateSettings = useModeStore((s) => s.updateSettings);
  const rememberDefault = useModeStore((s) => s.rememberDefault);
  const restore = useModeStore((s) => s.restore);
  const syncFromApi = useModeStore((s) => s.syncFromApi);

  useEffect(() => {
    document.title = "Настройки AI · ADOS Enterprise";
    void syncFromApi();
  }, [syncFromApi]);

  return (
    <WorkspaceLayout>
      <div className="mx-auto flex max-w-3xl flex-col gap-4 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">Настройки режима</h1>
            <p className="text-sm text-[var(--ew-muted)]">
              Human First — AI не навязывается. Вы выбираете режим работы.
            </p>
          </div>
          <ModeIndicator />
        </div>

        <Card title="Активный режим">
          <ModeSwitch />
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded-md border border-[var(--ew-border)] px-3 py-1.5 text-sm"
              onClick={() => rememberDefault()}
              data-testid="mode-remember"
            >
              📌 Запомнить режим
            </button>
            <button
              type="button"
              className="rounded-md border border-[var(--ew-border)] px-3 py-1.5 text-sm"
              onClick={() => restore()}
              data-testid="mode-restore"
            >
              Восстановить сессию
            </button>
            <Link to="/ai-command" className="rounded-md border border-[var(--ew-border)] px-3 py-1.5 text-sm">
              AI Command Center
            </Link>
          </div>
        </Card>

        <Card title="Параметры">
          <ul className="flex flex-col gap-3">
            {TOGGLES.map((item) => (
              <li key={item.key} className="flex items-center justify-between gap-3">
                <span className="text-sm">{item.label}</span>
                <Switch
                  checked={Boolean(settings[item.key])}
                  onChange={(v) => updateSettings({ [item.key]: v })}
                  label={item.label}
                />
              </li>
            ))}
          </ul>
        </Card>

        <Card title="Безопасность">
          <p className="text-sm text-[var(--ew-muted)]">
            Удаление, оплата, экспорт, отправка сообщений, публикация, запуск рекламы и изменение
            настроек всегда требуют подтверждения пользователя — во всех режимах.
          </p>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
