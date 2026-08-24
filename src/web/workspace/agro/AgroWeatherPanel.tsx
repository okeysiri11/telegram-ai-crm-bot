/**
 * AGRO Weather Intelligence Dashboard — existing Agro → Погода section.
 * Values come from /api/agro-ops/v1/weather/* (Open-Meteo). No invented climate normals.
 */

import { useEffect, useMemo, useState } from "react";
import { Button, Card } from "@/ui";
import { agroOpsGet, agroOpsPost, pick } from "../business-ops/opsApi";
import { AgroUkraineMap, type WeatherLayer } from "./AgroUkraineMap";
import "./agroWeather.css";

type Row = Record<string, unknown>;

const TABS = [
  { id: "map", label: "Карта" },
  { id: "d7", label: "7 дней" },
  { id: "d30", label: "30 дней" },
  { id: "risks", label: "Агро-риски" },
  { id: "recs", label: "Рекомендации" },
  { id: "history", label: "История" },
] as const;

const LAYERS: { id: WeatherLayer; label: string }[] = [
  { id: "agro_risk", label: "Агро-риск" },
  { id: "temperature", label: "Температура" },
  { id: "precip", label: "Осадки" },
  { id: "humidity", label: "Влажность" },
  { id: "wind", label: "Ветер" },
  { id: "drought", label: "Засуха" },
  { id: "frost", label: "Заморозки" },
];

const WEEKDAYS = ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"];

function historyCopy(tab: string, history: Row): string {
  if (tab === "today") {
    return (history.today as Row | undefined)?.ok
      ? "Есть свежие наблюдения на сегодня."
      : "Нет актуальных погодных данных по этому региону.";
  }
  if (tab === "days_7") {
    const block = (history.days_7 as Row | undefined) || {};
    if (block.text_ru) return String(block.text_ru);
    if (block.precip != null) return `Осадки за 7 дней: ${block.precip} mm`;
    return "Недостаточно данных для сравнения с климатической нормой.";
  }
  if (tab === "days_30") {
    return String((history.days_30 as Row | undefined)?.text_ru || "Недостаточно данных для сравнения с климатической нормой.");
  }
  return String((history.season as Row | undefined)?.text_ru || "Недостаточно данных для сравнения с климатической нормой.");
}

function levelClass(level: unknown) {
  const v = String(level || "");
  if (v === "High" || v === "high_risk") return "agro-wx-risk-high";
  if (v === "Medium" || v === "caution") return "agro-wx-risk-medium";
  if (v === "Low" || v === "favorable" || v === "recommended") return "agro-wx-risk-low";
  return "text-[var(--ew-muted)]";
}

function weatherIcon(code: unknown, label?: unknown) {
  const n = Number(code);
  if (Number.isFinite(n)) {
    if (n === 0 || n === 1) return "☀️";
    if (n <= 3) return "⛅";
    if (n <= 48) return "🌫";
    if (n <= 67 || (n >= 80 && n <= 82)) return "🌧";
    if (n <= 77 || n === 85 || n === 86) return "❄️";
    if (n >= 95) return "⛈";
  }
  const t = String(label || "").toLowerCase();
  if (t.includes("дожд") || t.includes("ливень")) return "🌧";
  if (t.includes("ясно")) return "☀️";
  return "🌤";
}

function fmtTemp(v: unknown) {
  if (v == null || v === "") return null;
  const n = Number(v);
  if (!Number.isFinite(n)) return null;
  return `${n > 0 ? "+" : ""}${n}°C`;
}

function weekday(date: string) {
  const d = new Date(`${date}T00:00:00Z`);
  if (Number.isNaN(d.getTime())) return "—";
  return WEEKDAYS[d.getUTCDay()];
}

function metricLine(label: string, value: unknown, unit: string) {
  if (value == null || value === "") return `${label}: нет данных`;
  return `${label}: ${value}${unit}`;
}

export function AgroWeatherPanel(props: {
  headers: Record<string, string>;
  onOpenSettings?: () => void;
}) {
  const [dash, setDash] = useState<Row | null>(null);
  const [drawer, setDrawer] = useState<Row | null>(null);
  const [cropExplain, setCropExplain] = useState<Row | null>(null);
  const [cellExplain, setCellExplain] = useState<Row | null>(null);
  const [historyTab, setHistoryTab] = useState("today");
  const [tab, setTab] = useState<(typeof TABS)[number]["id"]>("map");
  const [layer, setLayer] = useState<WeatherLayer>("agro_risk");
  const [crop, setCrop] = useState("general");
  const [crops, setCrops] = useState<Row[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState("");
  const [forecastOpen, setForecastOpen] = useState(false);
  const [selectedMacro, setSelectedMacro] = useState<string | null>(null);

  async function reload(extraCrop?: string) {
    setLoading("map");
    setError("");
    const q = extraCrop && extraCrop !== "general" ? `?crop=${encodeURIComponent(extraCrop)}` : "";
    const dashRes = await agroOpsGet("/weather/dashboard", props.headers);
    const overRes = await agroOpsGet(`/weather/overview${q}`, props.headers);
    setLoading("");
    if (!dashRes.ok && !overRes.ok) {
      setError("Свежие погодные данные временно недоступны.");
      return;
    }
    const merged = {
      ...((dashRes.ok ? dashRes.json : {}) as Row),
      ...((overRes.ok && !(overRes.json as Row)?.items ? overRes.json : {}) as Row),
    } as Row;
    if (overRes.ok && (overRes.json as Row)?.region_cards) {
      Object.assign(merged, overRes.json);
    }
    if (!merged.ok && dashRes.ok) Object.assign(merged, dashRes.json as Row);
    setDash(merged.ok || merged.oblasts || merged.macros ? merged : ((dashRes.json || overRes.json || {}) as Row));
  }

  useEffect(() => {
    void reload(crop);
  }, [props.headers]);

  useEffect(() => {
    void (async () => {
      const r = await agroOpsGet("/crops/directory", props.headers);
      setCrops((((r.json as { items?: Row[] })?.items) || []) as Row[]);
    })();
  }, [props.headers]);

  async function openOblast(oblastId: string) {
    setLoading(oblastId);
    setSelectedMacro(null);
    const q = crop !== "general" ? `?crop=${encodeURIComponent(crop)}` : "";
    const r = await agroOpsGet(`/weather/regions/${oblastId}${q}`, props.headers);
    setLoading("");
    if (!r.ok) {
      setError("Нет данных по области");
      return;
    }
    setDrawer((r.json || {}) as Row);
  }

  async function openMacro(macroId: string) {
    setSelectedMacro(macroId);
    const r = await agroOpsGet(`/weather/forecast?region=${encodeURIComponent(macroId)}&days=7`, props.headers);
    const risk = await agroOpsGet(`/weather/agro-risk?region=${encodeURIComponent(macroId)}&crop=${encodeURIComponent(crop)}`, props.headers);
    const recs = await agroOpsGet(`/weather/recommendations?region=${encodeURIComponent(macroId)}&crop=${encodeURIComponent(crop)}`, props.headers);
    const outlook = await agroOpsGet(`/weather/outlook?region=${encodeURIComponent(macroId)}&days=30`, props.headers);
    const item = ((r.json as Row) || {}).item as Row | undefined;
    const card = (((dash?.region_cards as Row[]) || []).find((c) => c.id === macroId) || {}) as Row;
    setDrawer({
      ok: true,
      item: {
        ...(item || {}),
        id: macroId,
        label_ru: card.title_ru || item?.label_ru,
        temperature: card.temperature ?? item?.temperature,
        humidity: card.humidity ?? item?.humidity,
        wind_speed: card.wind_speed ?? item?.wind_speed,
        precip_7: card.precip_7 ?? item?.precip_7,
        agro_risk: (risk.json as Row)?.agro_risk || card.agro_risk,
        is_macro: true,
      },
      forecast_7: ((r.json as Row).forecast as Row[]) || [],
      monthly_outlook_ru: (outlook.json as Row)?.monthly_outlook_ru,
      outlook_30d: (outlook.json as Row)?.outlook_30d,
      agro_risk: (risk.json as Row)?.agro_risk,
      risk: (risk.json as Row)?.agro_risk,
      recommendations: (recs.json as Row)?.recommendations,
      crop_impact: [],
    });
  }

  async function refresh() {
    setLoading("refresh");
    await agroOpsPost("/weather/refresh", {}, props.headers);
    await reload(crop);
    setLoading("");
  }

  async function changeCrop(next: string) {
    setCrop(next);
    await reload(next);
    const oblastId = String(((drawer?.item as Row | undefined)?.id) || "");
    if (oblastId && !(drawer?.item as Row | undefined)?.is_macro) {
      await openOblast(oblastId);
    } else if (selectedMacro) {
      await openMacro(selectedMacro);
    }
  }

  const oblasts = useMemo(() => {
    const fromMap = (((dash?.map as Row | undefined)?.regions as Row[]) || []) as Row[];
    const fromList = (dash?.oblasts as Row[]) || [];
    const byId = new Map<string, Row>();
    for (const row of fromList) byId.set(String(row.id), row);
    for (const row of fromMap) {
      const id = String(row.id);
      byId.set(id, { ...(byId.get(id) || {}), ...row });
    }
    return [...byId.values()];
  }, [dash]);

  const item = (drawer?.item as Row | undefined) || {};
  const history = (dash?.history as Row | undefined) || {};
  const last = (dash?.last_updated as Row | undefined) || {};
  const conf = (dash?.confidence as Row | undefined) || {};
  const fallback = dash?.fallback as Row | undefined;
  const current = (item.current as Row | undefined) || item;
  const forecast = (((drawer?.forecast_7 as Row[]) || (item.forecast_7 as Row[]) || []) as Row[]);
  const outlook = ((drawer?.outlook_30d as Row | undefined) || (dash?.outlook_30d as Row | undefined) || {}) as Row;
  const recs = (((drawer?.recommendations as Row[]) || (dash?.recommendations as Row[]) || []) as Row[]);
  const calendar = (((dash?.calendar as Row[]) || []) as Row[]);
  const selectedId = item.is_macro ? null : String(item.id || "") || null;

  function panelTitle() {
    if (item.label_ru) return String(item.label_ru);
    if (selectedMacro) {
      const card = ((dash?.region_cards as Row[]) || []).find((c) => c.id === selectedMacro);
      return String(card?.title_uk || card?.title_ru || "Регион");
    }
    return "Выберите область или регион";
  }

  return (
    <div className="agro-wx" data-testid="agro-weather-panel">
      <div className="agro-wx-head">
        <div>
          <h2 className="agro-wx-title" data-testid="agro-weather-title">
            ПОГОДА И АГРО-ПРОГНОЗ
          </h2>
          <label className="eds-type-small mt-2 block">
            Культура:{" "}
            <select
              data-testid="agro-weather-crop-select"
              className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
              value={crop}
              onChange={(e) => void changeCrop(e.target.value)}
            >
              <option value="general">Общий обзор</option>
              {crops.map((c) => (
                <option key={String(c.name)} value={String(c.name)}>
                  {String(c.name)}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="agro-wx-actions">
          <span className="eds-type-small text-[var(--ew-muted)]" data-testid="agro-weather-updated">
            Последнее обновление: {String(last.display_ru || "—")}
          </span>
          <Button size="sm" onClick={() => void refresh()} disabled={loading === "refresh"} data-testid="agro-weather-refresh">
            Обновить данные
          </Button>
          <Button
            size="sm"
            variant="ghost"
            data-testid="agro-weather-settings"
            onClick={() => props.onOpenSettings?.()}
          >
            Настройки
          </Button>
        </div>
      </div>

      <div className="agro-wx-tabs" data-testid="agro-weather-tabs">
        {TABS.map((t) => (
          <Button key={t.id} size="sm" variant={tab === t.id ? "primary" : "ghost"} onClick={() => setTab(t.id)}>
            {t.label}
          </Button>
        ))}
      </div>

      {fallback && (fallback.used || fallback.message_ru) ? (
        <div className="agro-wx-banner" data-testid="agro-weather-fallback">
          {String(fallback.message_ru || "Свежие погодные данные временно недоступны.")}
        </div>
      ) : null}
      {error ? (
        <div className="agro-wx-banner" data-testid="agro-weather-error">
          {error}{" "}
          <Button size="sm" variant="ghost" onClick={() => void reload(crop)}>
            Повторить
          </Button>
        </div>
      ) : null}

      <div className="agro-wx-tabs" data-testid="agro-weather-layers">
        <span className="eds-type-small text-[var(--ew-muted)]">Режим отображения:</span>
        {LAYERS.map((l) => (
          <Button key={l.id} size="sm" variant={layer === l.id ? "primary" : "ghost"} onClick={() => setLayer(l.id)}>
            {l.label}
          </Button>
        ))}
      </div>

      {tab === "map" || tab === "d7" || tab === "d30" || tab === "risks" || tab === "recs" || tab === "history" ? (
        <div className="agro-wx-stage">
          <div>
            <AgroUkraineMap
              oblasts={oblasts as { id?: string }[]}
              layer={layer}
              selectedId={selectedId}
              selectedMacro={selectedMacro}
              onSelect={(id) => void openOblast(id)}
              loading={loading === "map"}
            />
            <div className="agro-wx-legend mt-2" data-testid="agro-weather-legend">
              УРОВЕНЬ АГРО-РИСКА
              <span className="agro-wx-swatch" style={{ background: "#1a7f4c" }} /> Низкий
              <span className="agro-wx-swatch" style={{ background: "#c9a227" }} /> Умеренный
              <span className="agro-wx-swatch" style={{ background: "#c2410c" }} /> Высокий
            </div>
          </div>
          <aside className="agro-wx-panel" data-testid="agro-weather-side">
            {drawer || selectedMacro ? (
              <Button
                size="sm"
                variant="ghost"
                className="mb-2 min-h-11"
                data-testid="agro-weather-back"
                onClick={() => {
                  setDrawer(null);
                  setSelectedMacro(null);
                }}
              >
                ← Назад к карте
              </Button>
            ) : null}
            <div className="font-medium mb-1">{panelTitle()}</div>
            <div className="agro-wx-temp">{fmtTemp(current.temperature ?? item.temperature) || "—"}</div>
            <div className="eds-type-small mb-2 text-[var(--ew-muted)]">
              {String(current.weather_ru || item.weather_ru || (drawer ? "Текущие условия" : "Выберите область"))}
            </div>
            <div className="agro-wx-metrics">
              <div>{metricLine("Влажность", current.humidity ?? item.humidity, "%")}</div>
              <div>{metricLine("Ветер", current.wind_speed ?? item.wind_speed, " м/с")}</div>
              <div>{metricLine("Давление", current.pressure ?? item.pressure, " гПа")}</div>
              <div>
                {item.soil_temperature != null || current.soil_temperature != null
                  ? `Температура почвы: ${item.soil_temperature ?? current.soil_temperature}°C`
                  : "Температура почвы: нет данных"}
              </div>
              <div>{metricLine("Вероятность осадков", current.precip_probability ?? item.precip_probability, "%")}</div>
            </div>
            {drawer ? (
              <div className="mt-2 eds-type-small" data-testid="agro-weather-drawer">
                {item.missing ? <p data-testid="agro-weather-missing">{String(item.status_ru || drawer.monthly_outlook_ru)}</p> : null}
                <div data-testid="agro-weather-temp">
                  Температура: {item.temperature != null ? `${item.temperature} °C` : String(item.status_ru || "Нет актуальных погодных данных по этому региону.")}
                </div>
                <div data-testid="agro-weather-rain">Осадки: {item.rain != null ? `${item.rain} mm` : item.precip_7 != null ? `${item.precip_7} mm / 7д` : "нет данных"}</div>
                <div data-testid="agro-weather-forecast">
                  Прогноз 7 дней:{" "}
                  {forecast.length
                    ? forecast.map((d) => `${d.date}: ${d.tmax ?? "—"}° / ${d.precip ?? "—"} mm`).join("; ")
                    : "нет данных"}
                </div>
                <div data-testid="agro-weather-outlook">
                  На месяц: {String(drawer.monthly_outlook_ru || (outlook.temperature_trend as Row | undefined)?.text_ru || "Недостаточно данных для сравнения с климатической нормой.")}
                </div>
                <div data-testid="agro-weather-risk">
                  Риск: {String(((drawer.risk as Row | undefined) || (item.agro_risk as Row | undefined))?.label_ru || "нет данных")}
                </div>
                <div data-testid="agro-weather-crop-impact">
                  {(drawer.crop_impact as Row[] | undefined)?.map((c) => (
                    <div key={String(c.crop_id)}>
                      {String(c.crop_ru || c.label_ru)}: {String(c.level || "Missing")} · {String(c.explanation_ru)}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="eds-type-small text-[var(--ew-muted)]">Клик по области откроет фактические условия.</p>
            )}
            <div className="mt-3 eds-type-small" data-testid="agro-weather-confidence">
              <div>УРОВЕНЬ УВЕРЕННОСТИ ПРОГНОЗА</div>
              <div className="text-lg font-medium">
                {conf.score != null ? `${conf.score}%` : "—"} {String(conf.label_ru || "")}
              </div>
              <div>{String(conf.text_ru || "Прогноз основан на данных 0 источников")}</div>
            </div>
          </aside>
        </div>
      ) : null}

      {tab === "d7" || tab === "map" ? (
        <Card title="Прогноз на 7 дней">
          <div className="agro-wx-days" data-testid="agro-weather-forecast-grid">
            {(forecast.length ? forecast : [{ date: "—" }]).slice(0, 7).map((d, i) => (
              <div key={String(d.date || i)} className="agro-wx-day">
                <div>{d.date && d.date !== "—" ? weekday(String(d.date)) : "—"}</div>
                <div className="agro-wx-icon">{weatherIcon(d.weather_code, d.weather_ru)}</div>
                <div>
                  {d.tmin != null || d.tmax != null ? `${d.tmin ?? "—"}° / ${d.tmax ?? "—"}°` : "нет данных"}
                </div>
                <div>{d.precip != null ? `${d.precip} мм` : "осадки: нет данных"}</div>
                <div>{d.precip_probability != null ? `${d.precip_probability}%` : ""}</div>
                <div>{d.wind != null ? `${d.wind} м/с` : ""}</div>
              </div>
            ))}
          </div>
          <Button className="mt-2" size="sm" variant="ghost" onClick={() => setForecastOpen((v) => !v)} data-testid="agro-weather-forecast-more">
            Подробнее
          </Button>
          {forecastOpen ? (
            <div className="mt-2 eds-type-small" data-testid="agro-weather-forecast-detail">
              {forecast.map((d) => (
                <div key={String(d.date)}>
                  {String(d.date)} · {String(d.weather_ru || "—")} · max {String(d.tmax ?? "нет данных")} · осадки {String(d.precip ?? "нет данных")}
                </div>
              ))}
            </div>
          ) : null}
        </Card>
      ) : null}

      {tab === "d30" ? (
        <Card title="ПРОГНОЗ НА 30 ДНЕЙ">
          <p className="eds-type-small text-[var(--ew-muted)]">{String(outlook.provider_horizon_note_ru || "Агрегированная оценка, не суточный прогноз на 30 дней.")}</p>
          <div className="grid gap-2 eds-type-small mt-2" data-testid="agro-weather-outlook-block">
            <p>Температура: {String((outlook.temperature_trend as Row | undefined)?.text_ru || "Недостаточно данных для уверенного прогноза.")}</p>
            <p>Осадки: {String((outlook.precipitation_trend as Row | undefined)?.text_ru || "Недостаточно данных для уверенного прогноза.")}</p>
            <p>Засуха: {String((outlook.drought_probability as Row | undefined)?.text_ru || "Недостаточно данных для уверенного прогноза.")}</p>
            <p>Продолжительные дожди: {String((outlook.excessive_rain_probability as Row | undefined)?.text_ru || "Недостаточно данных для уверенного прогноза.")}</p>
            <p>Риск жары: {String((outlook.heat_probability as Row | undefined)?.text_ru || "Недостаточно данных для уверенного прогноза.")}</p>
            <p>Риск заморозков: {String((outlook.frost_probability as Row | undefined)?.text_ru || "Недостаточно данных для уверенного прогноза.")}</p>
            <p>Влажность: {String((outlook.moisture as Row | undefined)?.text_ru || "Недостаточно данных для уверенного прогноза.")}</p>
            <p>Агро-риск: {String((outlook.agro_risk as Row | undefined)?.label_ru || "Недостаточно данных для уверенного прогноза.")}</p>
          </div>
        </Card>
      ) : null}

      {tab === "recs" || tab === "map" ? (
        <>
          <Card title="Агро-рекомендации">
            <p className="eds-type-caption mb-2">
              {crop === "general" ? "Общий погодный агро-индикатор — культура не выбрана." : `Контекст культуры: ${crop}. Фаза роста и тип почвы пока не подключены.`}
            </p>
            <div className="agro-wx-rec-grid" data-testid="agro-weather-recs">
              {recs.map((r) => (
                <div key={String(r.id)} className="agro-wx-card" data-testid={`agro-weather-rec-${pick(r, "id")}`}>
                  <div>
                    {String(r.icon || "")} {String(r.category_ru || "").toUpperCase()}
                  </div>
                  <div className={levelClass(r.status)}>{String(r.status_ru)}</div>
                  {r.window_ru ? <div>Оптимальное окно: {String(r.window_ru)}</div> : null}
                  {Array.isArray(r.dates) && (r.dates as string[]).length ? <div>Дни: {(r.dates as string[]).join(", ")}</div> : null}
                  <div className="eds-type-caption">{String(r.reason_ru || "")}</div>
                </div>
              ))}
            </div>
          </Card>
          <Card title="АГРО-КАЛЕНДАРЬ РАБОТ">
            <div className="agro-wx-cal-grid" data-testid="agro-weather-calendar">
              {calendar.map((c) => (
                <div key={String(c.id)} className="agro-wx-card">
                  <div className="font-medium">{String(c.title_ru).toUpperCase()}</div>
                  <div className={levelClass(c.status)}>{String(c.status_ru)}</div>
                  <div>{c.window_ru ? String(c.window_ru) : "окно не определено"}</div>
                  <div className="eds-type-caption">{String(c.reason_ru || "")}</div>
                </div>
              ))}
            </div>
          </Card>
        </>
      ) : null}

      <div className="agro-wx-cards" data-testid="agro-weather-region-cards">
        {((dash?.region_cards as Row[]) || []).map((c) => (
          <button
            key={String(c.id)}
            type="button"
            className={`agro-wx-card ${selectedMacro === c.id ? "is-active" : ""}`}
            onClick={() => void openMacro(String(c.id))}
            data-testid={`agro-weather-macro-${pick(c, "id")}`}
          >
            <div className="font-medium">{String(c.title_ru || c.short_ru)}</div>
            <div className="text-xl">{fmtTemp(c.temperature) || "нет данных"}</div>
            <div className="eds-type-caption">{String(c.feel_ru || "")}</div>
            <div className="eds-type-small">Осадки 7 дней: {c.precip_7 != null ? `${c.precip_7} мм` : "нет данных"}</div>
            <div className="eds-type-small">Влажность: {c.humidity != null ? `${c.humidity}%` : "нет данных"}</div>
            <div className="eds-type-small">Ветер: {c.wind_speed != null ? `${c.wind_speed} м/с` : "нет данных"}</div>
            <div className={levelClass((c.agro_risk as Row | undefined)?.level)}>
              АГРО-РИСК: {String((c.agro_risk as Row | undefined)?.label_ru || "нет данных").toUpperCase()}
            </div>
          </button>
        ))}
      </div>

      <Card title="Сводка по макрорегионам">
        <div className="grid gap-2 lg:grid-cols-2 2xl:grid-cols-3" data-testid="agro-weather-macros">
          {((dash?.macros as Row[]) || []).map((m) => (
            <div key={String(m.macro_id)} className="border-b border-[var(--ew-border)] pb-2">
              <div className="font-medium">{String(m.title_ru)}</div>
              <p>Следующие 7 дней: {String(m.next_7_ru)}</p>
              <p>На месяц: {String(m.month_ru)}</p>
              <p>Риск: {String(m.risk_ru)}</p>
              <p>Возможное влияние: {String(m.impact_ru)}</p>
              <p>Что контролировать: {String(m.monitor_ru)}</p>
            </div>
          ))}
        </div>
      </Card>

      <Card title="Погода и культуры">
        <div className="grid gap-3" data-testid="agro-weather-crops">
          {((dash?.crops as Row[]) || []).map((cropRow) => (
            <div key={String(cropRow.id)}>
              <div className="font-medium">{String(cropRow.label_ru).toUpperCase()}</div>
              <div className="flex flex-wrap gap-2">
                {((cropRow.regions as Row[]) || []).map((reg) => (
                  <button
                    key={String(reg.macro_id)}
                    type="button"
                    className={`rounded border border-[var(--ew-border)] px-2 py-1 eds-type-small ${levelClass(reg.level)}`}
                    onClick={() => setCropExplain({ crop: cropRow.label_ru, ...reg })}
                  >
                    {String(reg.short_ru)}: {String(reg.label_ru)}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
        {cropExplain ? (
          <div className="mt-2 eds-type-small" data-testid="agro-weather-crop-explain">
            <p className="font-medium">
              {String(cropExplain.crop)} · {String(cropExplain.short_ru)}
            </p>
            <p>{String(cropExplain.explanation_ru)}</p>
            <Button size="sm" variant="ghost" onClick={() => setCropExplain(null)}>
              Закрыть
            </Button>
          </div>
        ) : null}
      </Card>

      <Card title="Матрица рисков">
        <div className="overflow-x-auto" data-testid="agro-weather-matrix">
          <table className="w-full eds-type-small">
            <thead>
              <tr>
                <th className="text-left">Регион</th>
                {(((dash?.matrix as Row | undefined)?.columns as Row[]) || []).map((c) => (
                  <th key={String(c.id)}>{String(c.label_ru || c.label_en || c.id)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(((dash?.matrix as Row | undefined)?.rows as Row[]) || []).map((row) => (
                <tr key={String(row.macro_id)} className="border-b border-[var(--ew-border)]">
                  <td>{String(row.label_ru || row.label_uk || row.label_en || row.macro_id)}</td>
                  {(((dash?.matrix as Row | undefined)?.columns as Row[]) || []).map((c) => {
                    const cell = ((row.cells as Row) || {})[String(c.id)] as Row | undefined;
                    return (
                      <td key={String(c.id)}>
                        <button
                          type="button"
                          className={`min-h-11 underline ${levelClass(cell?.level)}`}
                          onClick={() =>
                            setCellExplain({
                              region: row.label_ru || row.label_en,
                              crop: c.label_ru || c.label_en,
                              ...cell,
                            })
                          }
                        >
                          {String(cell?.label_ru || cell?.label_en || cell?.level || "Нет данных")}
                        </button>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {cellExplain ? (
          <div className="mt-2 eds-type-small" data-testid="agro-weather-matrix-explain">
            <p>
              {String(cellExplain.region)} / {String(cellExplain.crop)}: {String(cellExplain.label_ru)}
            </p>
            <p>{String(cellExplain.explanation_ru)}</p>
            <Button size="sm" variant="ghost" onClick={() => setCellExplain(null)}>
              Закрыть
            </Button>
          </div>
        ) : null}
      </Card>

      {tab === "risks" ? (
        <Card title="Агро-риски">
          <p className="eds-type-small">
            Цвет карты и карточки регионов считаются по агро-риску из фактических температуры, осадков, влажности и ветра.
          </p>
        </Card>
      ) : null}

      <Card title="История погоды">
        <div className="mb-2 flex flex-wrap gap-2" data-testid="agro-weather-history">
          {[
            ["today", "Сегодня"],
            ["days_7", "7 дней"],
            ["days_30", "30 дней"],
            ["season", "Сезон"],
          ].map(([id, label]) => (
            <Button key={id} size="sm" variant={historyTab === id ? "primary" : "ghost"} onClick={() => setHistoryTab(id)}>
              {label}
            </Button>
          ))}
        </div>
        <p className="eds-type-small">{historyCopy(historyTab, history)}</p>
        <p className="eds-type-caption mt-1">{String(history.note_ru || "")}</p>
      </Card>
    </div>
  );
}
