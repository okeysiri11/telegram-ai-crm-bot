/**
 * AGRO 2.0 — Settings information architecture.
 * Technical diagnostics live here, not on the intelligence home screen.
 */

import { useEffect, useState, type ReactNode } from "react";
import { Button, Card, Input } from "@/ui";
import { agroOpsGet, agroOpsPut, pick } from "../business-ops/opsApi";
import { FRESHNESS_RU, ROLE_RU } from "./agroLabels";

type Row = Record<string, unknown>;

const TABS: { id: string; label: string }[] = [
  { id: "general", label: "ОБЩИЕ" },
  { id: "sources", label: "ИСТОЧНИКИ ДАННЫХ" },
  { id: "intel", label: "АГРОРАЗВЕДКА" },
  { id: "analytics", label: "АНАЛИТИКА" },
  { id: "weather", label: "ПОГОДА" },
  { id: "schedule", label: "РАСПИСАНИЕ" },
  { id: "notifications", label: "УВЕДОМЛЕНИЯ" },
  { id: "diagnostics", label: "ДИАГНОСТИКА" },
];

export function AgroSettingsPanel(props: {
  headers: Record<string, string>;
  roleLabel: string;
  agroRole: string;
  providers: Row[];
  channels: Record<string, unknown>;
  canAdmin: boolean;
  initialTab?: string;
}) {
  const [tab, setTab] = useState(props.initialTab || "general");
  const [desk, setDesk] = useState<Row | null>(null);
  const [item, setItem] = useState<Row>({});
  const [msg, setMsg] = useState("");
  const [advanced, setAdvanced] = useState(false);

  async function reload() {
    const r = await agroOpsGet("/settings/desk", props.headers);
    const body = (r.json || {}) as Row;
    setDesk(body);
    setItem((body.item as Row) || {});
  }

  useEffect(() => {
    void reload();
  }, [props.headers]);

  async function save(patch: Row = {}) {
    const body = { ...item, ...patch };
    const r = await agroOpsPut("/settings/desk", body, props.headers);
    const j = r.json as { ok?: boolean; item?: Row; message_ru?: string };
    setMsg(j.ok ? "Сохранено" : j.message_ru || "Не удалось сохранить");
    if (j.ok) {
      setDesk(r.json as Row);
      setItem((j.item as Row) || body);
    }
  }

  const specialists = ((desk?.specialist_catalog as Row[]) || []) as Row[];
  const schedule = ((desk?.schedule as Row[]) || []) as Row[];
  const diagnostics = ((desk?.diagnostics as Row[]) || []) as Row[];
  const weatherProviders = props.providers.filter((p) => String(p.id).includes("weather") || String(p.category) === "weather");

  function pane(id: string, children: ReactNode) {
    if (tab !== id) return null;
    return (
      <div data-testid={`agro-settings-tab-${id}`}>
        {children}
      </div>
    );
  }

  return (
    <div data-testid="agro-settings" className="grid gap-3 overflow-x-hidden">
      <div className="flex flex-wrap gap-1" data-testid="agro-settings-tabs">
        {TABS.map((t) => (
          <Button key={t.id} size="sm" variant={tab === t.id ? "primary" : "ghost"} onClick={() => setTab(t.id)}>
            {t.label}
          </Button>
        ))}
      </div>
      {msg ? <p className="eds-type-small">{msg}</p> : null}

      {pane(
        "general",
        <>
          <Card title="Пользователи и роли">
            <p className="eds-type-small">Текущая роль: {ROLE_RU[props.agroRole] || props.roleLabel}</p>
            <p className="eds-type-small">Директор видит всё. Бухгалтер работает со счетами и оплатами, не удаляет компании и не меняет источники разведки.</p>
          </Card>
          <Card title="Источники данных">
            <ul className="eds-type-small" data-testid="agro-settings-sources">
              {props.providers.map((p) => (
                <li key={pick(p, "id")}>
                  {pick(p, "label_ru")}: {FRESHNESS_RU[pick(p, "status")] || FRESHNESS_RU[pick(p, "health_state")] || pick(p, "status") || pick(p, "health_state")}
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Уведомления">
            <ul className="eds-type-small">
              {Object.values(props.channels).map((ch) => {
                const c = ch as Row;
                return (
                  <li key={String(c.id)}>
                    {String(c.label_ru)} · {c.connected ? "подключено" : "не настроено"}
                  </li>
                );
              })}
            </ul>
          </Card>
        </>,
      )}

      {pane(
        "sources",
        <Card title="Источники данных">
          <p className="eds-type-small">Подключение и проверка источников выполняются в Агро-разведке. Краткий статус — на вкладке Общие.</p>
        </Card>,
      )}

      {pane(
        "intel",
        <Card title="Агроразведка">
          <div className="grid gap-2 sm:grid-cols-2 eds-type-small" data-testid="agro-settings-intel">
            <label>
              Частота обновления
              <select className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1" value={String(item.refresh_frequency || "standard")} onChange={(e) => setItem((f) => ({ ...f, refresh_frequency: e.target.value }))}>
                <option value="fast">Часто</option>
                <option value="standard">Стандартно</option>
                <option value="slow">Редко</option>
              </select>
            </label>
            <label>
              Порог уверенности
              <Input type="number" value={String(item.confidence_threshold ?? 50)} onChange={(e) => setItem((f) => ({ ...f, confidence_threshold: Number(e.target.value) }))} />
            </label>
            <label>
              Длина обзора
              <select className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1" value={String(item.report_length || "standard")} onChange={(e) => setItem((f) => ({ ...f, report_length: e.target.value }))}>
                <option value="short">Кратко</option>
                <option value="standard">Стандартно</option>
                <option value="long">Подробно</option>
              </select>
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={Boolean(item.morning_report_enabled)} onChange={(e) => setItem((f) => ({ ...f, morning_report_enabled: e.target.checked }))} />
              Утренний обзор включён
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={Boolean(item.evening_report_enabled)} onChange={(e) => setItem((f) => ({ ...f, evening_report_enabled: e.target.checked }))} />
              Вечерний обзор включён
            </label>
            <p>Регионы: {((item.enabled_regions as string[]) || []).join(", ") || "все"}</p>
            <p>Культуры: {((item.enabled_commodities as string[]) || []).join(", ") || "все"}</p>
            <p>Приоритет источников: {((item.source_priority as string[]) || []).join(" → ")}</p>
          </div>
          {props.canAdmin ? (
            <Button className="mt-2" size="sm" onClick={() => void save()}>
              Сохранить
            </Button>
          ) : null}
        </Card>,
      )}

      {pane(
        "analytics",
        <Card title="Аналитика">
          <div className="eds-type-small" data-testid="agro-settings-analytics">
            <p className="mb-2">Детализация по умолчанию</p>
            {["short", "standard", "long"].map((id) => (
              <label key={id} className="mr-3">
                <input type="radio" name="analytics_detail" checked={String(item.analytics_detail || "standard") === id} onChange={() => setItem((f) => ({ ...f, analytics_detail: id }))} />{" "}
                {id === "short" ? "Кратко" : id === "long" ? "Подробно" : "Стандартно"}
              </label>
            ))}
            <p className="mt-3 mb-1">Аналитики</p>
            {specialists.map((s) => (
              <label key={String(s.id)} className="mr-3 block">
                <input
                  type="checkbox"
                  checked={Boolean(s.enabled)}
                  onChange={(e) => {
                    const next = { ...((item.specialists as Row) || {}), [String(s.id)]: e.target.checked };
                    setItem((f) => ({ ...f, specialists: next }));
                  }}
                />{" "}
                {String(s.label_en)}
              </label>
            ))}
          </div>
          {props.canAdmin ? (
            <Button className="mt-2" size="sm" onClick={() => void save()}>
              Сохранить
            </Button>
          ) : null}
        </Card>,
      )}

      {pane(
        "weather",
        <Card title="Погода">
          <div className="eds-type-small grid gap-2" data-testid="agro-settings-weather">
            <p>Основной провайдер: {String(item.weather_primary || "weather_provider")}</p>
            <p>Резервный провайдер: {String(item.weather_backup || "weather_provider_secondary")}</p>
            <label>
              Горизонт прогноза (дни)
              <Input type="number" value={String(item.forecast_horizon_days ?? 7)} onChange={(e) => setItem((f) => ({ ...f, forecast_horizon_days: Number(e.target.value) }))} />
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={item.crop_impact_enabled !== false} onChange={(e) => setItem((f) => ({ ...f, crop_impact_enabled: e.target.checked }))} />
              Влияние на культуры включено
            </label>
            <p>Регионы: {((item.enabled_regions as string[]) || []).join(", ")}</p>
            <ul data-testid="agro-settings-weather-status">
              {(weatherProviders.length ? weatherProviders : props.providers.filter((p) => pick(p, "id") === "weather_provider")).map((p) => (
                <li key={pick(p, "id")}>
                  {pick(p, "label_ru")}: {FRESHNESS_RU[pick(p, "health_state")] || pick(p, "health_state")}
                </li>
              ))}
            </ul>
            <div className="mt-3 border-t border-[var(--ew-border)] pt-2" data-testid="agro-settings-weather-diagnostics">
              <p className="font-medium">Источники и диагностика</p>
              <p>Основной бесплатный источник — Open-Meteo. Технические коды ответа и внутренности пайплайна скрыты с экрана Погоды.</p>
              <p>Если дополнительный производственный источник временно недоступен, на Погоде показывается понятное предупреждение, а не HTTP-код.</p>
              <Button size="sm" variant="ghost" className="mt-1" onClick={() => setTab("diagnostics")}>
                Открыть техническую диагностику
              </Button>
            </div>
          </div>
          {props.canAdmin ? (
            <Button className="mt-2" size="sm" onClick={() => void save()}>
              Сохранить
            </Button>
          ) : null}
        </Card>,
      )}

      {pane(
        "schedule",
        <Card title="Расписание">
          <div className="eds-type-small" data-testid="agro-settings-schedule">
            {(schedule.length ? schedule : []).map((job) => (
              <div key={pick(job, "id")} className="mb-2 flex flex-wrap items-center gap-2 border-b border-[var(--ew-border)] pb-2">
                <Input
                  type="time"
                  value={String(job.time_kyiv || "06:00")}
                  disabled={!props.canAdmin}
                  onChange={(e) => {
                    const next = schedule.map((j) => (pick(j, "id") === pick(job, "id") ? { ...j, time_kyiv: e.target.value } : j));
                    setDesk((d) => ({ ...(d || {}), schedule: next }));
                  }}
                />
                <span>
                  {String(job.time_kyiv || "")} {String(job.when_ru || "ежедневно")} · {pick(job, "label_ru")}
                </span>
              </div>
            ))}
            {props.canAdmin ? (
              <Button
                size="sm"
                onClick={async () => {
                  const jobs = schedule.map((j) => ({ id: j.id, time_kyiv: j.time_kyiv, cron_kyiv: j.cron_kyiv, label_ru: j.label_ru, when_ru: j.when_ru }));
                  await agroOpsPut("/scheduler", { jobs, timezone: "Europe/Kyiv" }, props.headers);
                  setMsg("Расписание сохранено");
                  await reload();
                }}
              >
                Сохранить время
              </Button>
            ) : null}
            <button type="button" className="mt-2 underline" onClick={() => setAdvanced((v) => !v)}>
              Расширенные настройки
            </button>
            {advanced ? (
              <pre className="mt-2 overflow-auto eds-type-caption" data-testid="agro-settings-schedule-cron">
                {schedule.map((j) => `${j.cron_kyiv || ""} · ${j.label_ru || ""}`).join("\n")}
              </pre>
            ) : null}
          </div>
        </Card>,
      )}

      {pane(
        "notifications",
        <Card title="Уведомления">
          <ul className="eds-type-small">
            {Object.values(props.channels).map((ch) => {
              const c = ch as Row;
              return (
                <li key={String(c.id)}>
                  {String(c.label_ru)} · {c.connected ? "подключено" : "не настроено"}
                </li>
              );
            })}
          </ul>
        </Card>,
      )}

      {pane(
        "diagnostics",
        <Card title="Диагностика">
          <div className="eds-type-small overflow-x-auto" data-testid="agro-settings-diagnostics">
            <p>Технические статусы источников. Не показываются на главном экране разведки.</p>
            <p>pipeline_version: {String(desk?.pipeline_version || "AGRO_1_9")}</p>
            <p>ux_version: {String(desk?.ux_version || "AGRO_2_0")}</p>
            <table className="mt-2 w-full">
              <thead>
                <tr>
                  <th className="text-left">Источник</th>
                  <th>HTTP</th>
                  <th>Состояние</th>
                  <th>Ошибка</th>
                </tr>
              </thead>
              <tbody>
                {diagnostics.map((d) => (
                  <tr key={String(d.provider_id)} className="border-b border-[var(--ew-border)]">
                    <td>{String(d.label_ru)}</td>
                    <td>{String(d.http_status || "—")}</td>
                    <td>{String(d.health_state || "—")}</td>
                    <td>{String(d.error || d.note_ru || "—")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>,
      )}
    </div>
  );
}
