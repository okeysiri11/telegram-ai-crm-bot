/**
 * АГРО-РАЗВЕДКА — live pipeline, history, stored reviews (1.4).
 */

import { useEffect, useState } from "react";
import { Button, Card, Input } from "@/ui";
import { agroOpsGet, agroOpsPost, pick } from "../business-ops/opsApi";
import { AgroCoverageCard } from "./AgroCoverageCard";
import { BIAS_RU, FRESHNESS_RU, GAP_SEVERITY_RU, HEALTH_HEX, HEALTH_STATE_COLOR, ru } from "./agroLabels";

type Row = Record<string, unknown>;

function kyivSlice(value: unknown): string {
  const s = String(value || "");
  if (!s || s === "—") return "—";
  return s.replace("T", " ").slice(0, 16);
}

function healthDotColor(row: Row): string {
  const named = String(row.health_color || HEALTH_STATE_COLOR[String(row.health_state || "")] || "gray");
  return HEALTH_HEX[named] || named || HEALTH_HEX.gray;
}

function isTech(text: unknown): boolean {
  return /HTTP\s+\d{3}|JSON\s+404|timeout|metadata_only|pipeline_version|METADATA_ONLY/i.test(String(text || ""));
}

export function AgroIntelPanel(props: {
  headers: Record<string, string>;
  canOperate: boolean;
  canIntel: boolean;
}) {
  const [providers, setProviders] = useState<Row[]>([]);
  const [report, setReport] = useState<Row | null>(null);
  const [history, setHistory] = useState<Row[]>([]);
  const [detail, setDetail] = useState<Row | null>(null);
  const [agents, setAgents] = useState<Row | null>(null);
  const [source, setSource] = useState<Row | null>(null);
  const [settings, setSettings] = useState<Row | null>(null);
  const [offer, setOffer] = useState("");
  const [recalc, setRecalc] = useState("");
  const [freshness, setFreshness] = useState<Row[]>([]);
  const [gaps, setGaps] = useState<string[]>([]);
  const [gapsStructured, setGapsStructured] = useState<Row[]>([]);
  const [coverage, setCoverage] = useState<Row | null>(null);
  const [sourceHealth, setSourceHealth] = useState<Row | null>(null);
  const [opCounts, setOpCounts] = useState<Row | null>(null);
  const [qualityFlags, setQualityFlags] = useState<Row[]>([]);
  const [anomalies, setAnomalies] = useState<Row[]>([]);
  const [ask, setAsk] = useState("");
  const [answer, setAnswer] = useState<Row | null>(null);
  const [importTitle, setImportTitle] = useState("");
  const [importSummary, setImportSummary] = useState("");
  const [customUrl, setCustomUrl] = useState("");
  const [customTrust, setCustomTrust] = useState("MEDIUM");
  const [schedule, setSchedule] = useState<Row | null>(null);
  const [brief, setBrief] = useState<Row | null>(null);
  const [riskCards, setRiskCards] = useState<Row[]>([]);
  const [opps, setOpps] = useState<Row[]>([]);
  const [changed, setChanged] = useState<Row[]>([]);
  const [openBiz, setOpenBiz] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");

  async function reload() {
    setLoading("providers");
    setError("");
    const p = await agroOpsGet("/providers", props.headers);
    if (!p.ok) setError("Не удалось загрузить источники");
    setProviders(((p.json as { items?: Row[] })?.items || []) as Row[]);
    const reports = await agroOpsGet("/reports", props.headers);
    const items = ((reports.json as { items?: Row[] })?.items || []) as Row[];
    setHistory(items);
    if (items[0]) setReport(items[0]);
    const runs = await agroOpsGet("/agents", props.headers);
    const stored = ((runs.json as { items?: Row[] })?.items || []) as Row[];
    if (stored[0]) setAgents(stored[0]);
    const dash = await agroOpsGet("/analytics/dashboard", props.headers);
    const dj = dash.json as {
      freshness?: Row[];
      gaps?: string[];
      gaps_structured?: Row[];
      coverage?: Row;
      source_health?: Row;
      operational_counts?: Row;
      quality_flags?: Row[];
      anomalies?: Row[];
    };
    setFreshness(dj.freshness || []);
    setGaps(dj.gaps || []);
    setGapsStructured(dj.gaps_structured || []);
    setCoverage((dj.coverage as Row | undefined) || (dj as Row));
    setSourceHealth(dj.source_health || null);
    setOpCounts(dj.operational_counts || null);
    setQualityFlags(dj.quality_flags || []);
    setAnomalies(dj.anomalies || []);
    setBrief((dj as { business_brief?: Row }).business_brief || null);
    setRiskCards((dj as { risk_cards?: Row[] }).risk_cards || []);
    setOpps((dj as { opportunity_cards?: Row[] }).opportunity_cards || []);
    setChanged((dj as { what_changed?: Row[] }).what_changed || []);
    const sched = await agroOpsGet("/scheduler", props.headers);
    setSchedule((sched.json || null) as Row | null);
    setLoading("");
  }

  useEffect(() => {
    void reload();
  }, [props.headers]);

  async function openLatest(kind: string) {
    setLoading(kind);
    setError("");
    setOffer("");
    const r = await agroOpsPost("/reports/generate", { kind, open_latest: true }, props.headers);
    const body = r.json as { ok?: boolean; item?: Row; offer_generate?: boolean; offer_recalculate?: boolean; message_ru?: string };
    setLoading("");
    if (body.item) {
      setReport(body.item);
      setMsg(String(body.item.title || "Обзор"));
      if (body.offer_recalculate) setRecalc(kind);
      return;
    }
    if (body.offer_generate) {
      setOffer(kind);
      setMsg(body.message_ru || "Обзора за сегодня нет. Сформировать сейчас?");
      return;
    }
    setError(body.message_ru || "Не удалось открыть обзор");
  }

  async function generate(kind: string, extra: Record<string, unknown> = {}) {
    setLoading(kind);
    setError("");
    setOffer("");
    const r = await agroOpsPost("/reports/generate", { kind, generate: true, ...extra }, props.headers);
    const body = r.json as { ok?: boolean; item?: Row; message_ru?: string };
    setLoading("");
    if (!r.ok && !body.ok) {
      setError(body.message_ru || "Не удалось сформировать обзор");
      return;
    }
    setReport(body.item || null);
    setMsg(body.item ? String(body.item.title || "Обзор готов") : "");
    await reload();
  }

  const sections = (report?.sections as Row[] | undefined) || [];
  const businessSections = (report?.business_sections as Row[] | undefined) || [];

  return (
    <div className="grid gap-3 overflow-x-hidden max-w-[1920px]" data-testid="agro-intel-panel">
      <Card title="Сводка">
        <p className="eds-type-small" data-testid="agro-intel-brief">
          {String(brief?.text_ru || "Получены свежие данные по погоде, валюте, торговле и рынкам.")}
        </p>
      </Card>
      <Card title="ЧТО ИЗМЕНИЛОСЬ ЗА 24 ЧАСА">
        <ul className="eds-type-small" data-testid="agro-what-changed">
          {changed.length === 0 ? <li>Существенных фактических изменений за 24 часа нет.</li> : null}
          {changed.map((c, i) => (
            <li key={i}>{String(c.text_ru)}</li>
          ))}
        </ul>
      </Card>
      <Card title="РИСКИ СЕГОДНЯ">
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3" data-testid="agro-risk-cards">
          {riskCards.length === 0 ? <p className="eds-type-small">Отдельных подтверждённых рисков сейчас нет.</p> : null}
          {riskCards.map((c) => (
            <div key={String(c.title_ru)} className="rounded border border-[var(--ew-border)] p-2">
              <div className="font-medium">{String(c.title_ru)} · {String(c.severity)}</div>
              <p className="eds-type-small">{String(c.summary_ru)}</p>
              <p className="eds-type-caption">Почему: {String(c.why_ru)}</p>
              <p className="eds-type-caption">Контроль: {String(c.monitor_ru)}</p>
            </div>
          ))}
        </div>
      </Card>
      <Card title="ВОЗМОЖНОСТИ">
        <div className="grid gap-2 sm:grid-cols-2" data-testid="agro-opportunity-cards">
          {opps.length === 0 ? <p className="eds-type-small">Потенциальных возможностей по совместимым рядам нет.</p> : null}
          {opps.map((c, i) => (
            <div key={i} className="rounded border border-[var(--ew-border)] p-2 eds-type-small">
              <div>Потенциальная возможность</div>
              <div>Регион: {String(c.region || "—")}</div>
              <div>Культура: {String(c.commodity || "—")}</div>
              <div>Причина: {String(c.reason_ru || "")}</div>
              <div>Сигнал: {String(c.signal_ru || "")}</div>
              <div>Confidence: {String(c.confidence ?? "—")}</div>
            </div>
          ))}
        </div>
      </Card>
      <details>
        <summary className="cursor-pointer eds-type-small">Подробнее</summary>
      <AgroCoverageCard coverage={coverage || undefined} />
      <Card title="ЗДОРОВЬЕ ИСТОЧНИКОВ">
        <div className="eds-type-small grid gap-1" data-testid="agro-source-health">
          <div>Healthy: {Number(sourceHealth?.healthy || 0)}</div>
          <div>Partial: {Number(sourceHealth?.partial || 0)}</div>
          <div>Needs key: {Number(sourceHealth?.needs_key || 0)}</div>
          <div>Optional: {Number(sourceHealth?.optional || 0)}</div>
          <div>Failed: {Number(sourceHealth?.failed || 0)}</div>
          <div>Last full refresh: {kyivSlice(sourceHealth?.last_full_refresh_at)}</div>
          <div>Refresh duration: {sourceHealth?.refresh_duration_sec != null ? `${Number(sourceHealth.refresh_duration_sec)} sec` : "—"}</div>
        </div>
      </Card>
      <Card title="Операционные счётчики">
        <div className="eds-type-small grid gap-1" data-testid="agro-operational-counts">
          <div>Числовых наблюдений: {Number(opCounts?.numeric_observations || 0)}</div>
          <div>Свежих &lt;24ч: {Number(opCounts?.fresh_24h || 0)}</div>
          <div>За 7 дней: {Number(opCounts?.last_7d || 0)}</div>
          <div>Исторических: {Number(opCounts?.historical || 0)}</div>
          <div>Ценовых: {Number(opCounts?.price || 0)}</div>
          <div>Погодных: {Number(opCounts?.weather || 0)}</div>
          <div>Торговых: {Number(opCounts?.trade || 0)}</div>
          <div>Логистических: {Number(opCounts?.logistics || 0)}</div>
        </div>
      </Card>
      <Card title="Проверка качества">
        <ul className="eds-type-small" data-testid="agro-quality-flags">
          {qualityFlags.length === 0 ? <li>Подозрительных записей нет. Ничего не удалялось.</li> : null}
          {qualityFlags.map((f, i) => (
            <li key={i}>
              {String(f.severity || "")} · {String(f.code || "")}: {String(f.text || "")}
              {f.kept ? " · сохранено" : ""}
            </li>
          ))}
        </ul>
      </Card>
      <Card title="Аномалии">
        <ul className="eds-type-small" data-testid="agro-anomalies">
          {anomalies.length === 0 ? <li>Недостаточно сопоставимых точек для ANOMALY.</li> : null}
          {anomalies.map((a, i) => (
            <li key={i}>{String(a.text || "")}</li>
          ))}
        </ul>
      </Card>
      <Card title="СВЕЖЕСТЬ ДАННЫХ">
        <div className="eds-type-small" data-testid="agro-intel-freshness">
          {freshness.length === 0 ? <p className="text-[var(--ew-muted)]">После опроса источников здесь будет возраст данных.</p> : null}
          {freshness.map((f) => (
            <div key={pick(f, "provider_id")}>
              {pick(f, "label_ru")}: {pick(f, "age_ru")}
            </div>
          ))}
        </div>
      </Card>
      <Card title="ПРОБЕЛЫ ДАННЫХ">
        <ul className="eds-type-small" data-testid="agro-intel-gaps">
          {(() => {
            const rows =
              gapsStructured.length > 0
                ? gapsStructured
                : (gaps.length ? gaps : ["Явных пробелов не зафиксировано."]).map((g) => ({ severity: "", text: g }));
            return rows.map((g) => {
              const text = String(g.text || g);
              const sev = String(g.severity || "");
              return (
                <li key={`${sev}-${text}`}>
                  {sev ? <strong className="mr-1">{GAP_SEVERITY_RU[sev] || sev}</strong> : null}
                  {text.startsWith("⚠") || text.startsWith("Явных") ? text : `⚠ ${text}`}
                </li>
              );
            });
          })()}
        </ul>
      </Card>
      </details>
      <Card title="Источники данных">
        <p className="eds-type-small mb-2 text-[var(--ew-muted)]">
          Внешние котировки, урожай и погода не выдумываются. Аналитики читают только нормализованные наблюдения.
        </p>
        <div className="mb-2 flex flex-wrap gap-2">
          <Button
            size="sm"
            disabled={!props.canIntel || Boolean(loading)}
            onClick={async () => {
              setLoading("refresh");
              setError("");
              const r = await agroOpsPost("/providers/refresh-all", {}, props.headers);
              const j = r.json as { ok?: boolean; message_ru?: string };
              setLoading("");
              if (!r.ok && !j.ok) setError(j.message_ru || "Опрос источников не удался");
              else setMsg("Опрос всех источников завершён");
              await reload();
            }}
          >
            Обновить все
          </Button>
          <Button
            size="sm"
            variant="ghost"
            disabled={!props.canIntel || Boolean(loading)}
            onClick={async () => {
              setLoading("recalculate");
              setError("");
              const r = await agroOpsPost("/analytics/run", { analysis_type: "operational" }, props.headers);
              const j = r.json as { ok?: boolean; message_ru?: string };
              setLoading("");
              if (!r.ok && !j.ok) setError(j.message_ru || "Пересчёт анализа не удался");
              else setMsg("Анализ пересчитан по сохранённым данным, без нового опроса сети");
              await reload();
            }}
          >
            Пересчитать анализ
          </Button>
          {loading ? <span className="eds-type-small" data-testid="agro-intel-loading">Загрузка: {loading}</span> : null}
        </div>
        {error ? <p className="eds-type-small text-[var(--ew-danger)]" data-testid="agro-intel-error">{error}</p> : null}
        <div className="overflow-x-auto" data-testid="agro-intel-providers">
          <table className="w-full eds-type-small">
            <thead>
              <tr>
                <th className="text-left">Источник</th>
                <th>Категория</th>
                <th>Статус</th>
                <th>Тип данных</th>
                <th>Market usable</th>
                <th>Последнее обновление</th>
                <th>Наблюдений</th>
                <th>Свежесть</th>
                <th>Ошибки</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {providers.map((p) => (
                <tr key={pick(p, "id")} className="border-b border-[var(--ew-border)]">
                  <td>
                    <button type="button" className="underline" onClick={async () => {
                      const r = await agroOpsGet(`/providers/${pick(p, "id")}`, props.headers);
                      setSource((r.json as { item?: Row; observations?: Row[] }) || p);
                    }}>
                      {pick(p, "label_ru", "name")}
                    </button>
                  </td>
                  <td>{pick(p, "group", "category")}</td>
                  <td>
                    <span
                      data-testid={`agro-health-${pick(p, "id")}`}
                      data-health-color={String(p.health_color || HEALTH_STATE_COLOR[pick(p, "health_state")] || "gray")}
                      style={{ color: healthDotColor(p) }}
                    >
                      ●
                    </span>{" "}
                    {FRESHNESS_RU[pick(p, "health_state")] || FRESHNESS_RU[pick(p, "connection_status")] || FRESHNESS_RU[pick(p, "status")] || (isTech(p.note_ru) ? "см. диагностику" : pick(p, "note_ru"))}
                  </td>
                  <td>{pick(p, "data_type_ru", "data_type") || "—"}</td>
                  <td>{p.market_usable ? "да" : "нет"}</td>
                  <td>{kyivSlice(p.last_success_at)}</td>
                  <td>{String(p.observation_count ?? 0)}</td>
                  <td>{FRESHNESS_RU[pick(p, "freshness")] || pick(p, "freshness") || "—"}</td>
                  <td>{isTech(p.error) || isTech(p.note_ru) ? "см. диагностику" : String(p.error || "—")}</td>
                  <td>
                    <div className="flex flex-wrap gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        disabled={!props.canIntel}
                        data-testid={`agro-source-probe-${pick(p, "id")}`}
                        onClick={async () => {
                          setLoading(pick(p, "id"));
                          const r = await agroOpsPost(`/providers/${pick(p, "id")}/probe`, {}, props.headers);
                          const body = r.json as { item?: Row; message_ru?: string };
                          setLoading("");
                          setMsg(body.item ? String(body.item.note_ru || "Проверка завершена") : body.message_ru || "Ошибка проверки");
                          await reload();
                        }}
                      >
                        Проверить
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        data-testid={`agro-source-latest-${pick(p, "id")}`}
                        onClick={async () => {
                          const r = await agroOpsGet(`/providers/${pick(p, "id")}`, props.headers);
                          setSource((r.json as { item?: Row; observations?: Row[] }) || p);
                        }}
                      >
                        Последние данные
                      </Button>
                      {p.url ? (
                        <a className="eds-type-small underline" href={String(p.url)} target="_blank" rel="noreferrer" data-testid={`agro-source-open-${pick(p, "id")}`}>
                          Открыть источник
                        </a>
                      ) : null}
                      <Button size="sm" variant="ghost" data-testid={`agro-source-settings-${pick(p, "id")}`} onClick={() => setSettings(p)}>Настройки</Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {source ? (
        <Card title={`Источник: ${String((source.item as Row | undefined)?.label_ru || (source as Row).label_ru || "")}`}>
          <div className="eds-type-small" data-testid="agro-intel-source-drawer">
            <div>Статус: {String((source.item as Row | undefined)?.health_state || (source.item as Row | undefined)?.connection_status || "—")}</div>
            <div>URL: {String((source.item as Row | undefined)?.url || "—")}</div>
            <div>Адаптер: {String((source.item as Row | undefined)?.adapter_type || "—")}</div>
            <div>Получено: {String(((source.observations as Row[]) || []).length)} наблюдения</div>
            <div>Последнее обновление: {kyivSlice((source.item as Row | undefined)?.last_success_at)}</div>
            <div>Данные: {String((source.item as Row | undefined)?.receives_ru || (source.item as Row | undefined)?.category || "—")}</div>
            <div>Ошибка: {String((source.item as Row | undefined)?.error || "нет")}</div>
            <ul className="mt-2">
              {((source.observations as Row[]) || []).slice(0, 12).map((o) => (
                <li key={pick(o, "id")}>{pick(o, "title", "raw_value")} · {String(o.published_at || "").slice(0, 16)}</li>
              ))}
            </ul>
            <Button className="mt-2" size="sm" variant="ghost" onClick={() => setSource(null)}>Закрыть</Button>
          </div>
        </Card>
      ) : null}

      {settings ? (
        <Card title={`Настройки: ${pick(settings, "label_ru")}`}>
          <div className="eds-type-small">
            <div>URL: {String(settings.url || "не задан")}</div>
            <div>Каденс: {String(settings.cadence || "—")}</div>
            <div>Лицензия: {String(settings.license_note_ru || "—")}</div>
          </div>
          <Button className="mt-2" size="sm" variant="ghost" onClick={() => setSettings(null)}>Закрыть</Button>
        </Card>
      ) : null}

      <Card title="Обзоры">
        <div className="flex flex-wrap gap-2">
          <Button size="sm" disabled={!props.canIntel || Boolean(loading)} onClick={() => void openLatest("morning")}>
            Утренний обзор
          </Button>
          <Button size="sm" disabled={!props.canIntel || Boolean(loading)} onClick={() => void openLatest("evening")}>
            Вечерний обзор
          </Button>
          <Button size="sm" variant="ghost" disabled={!props.canIntel} onClick={() => void generate("weekly")}>
            Недельный прогноз
          </Button>
          <Button size="sm" variant="ghost" disabled={!props.canIntel} onClick={() => void generate("outlook")}>
            Перспектива 1–2 месяца
          </Button>
          <Button size="sm" variant="ghost" disabled={!props.canIntel || !report} onClick={() => void generate(String(report?.report_kind || "morning_on_demand"), { recalculate: true })}>
            Пересчитать
          </Button>
        </div>
        {offer ? (
          <div className="mt-2">
            <p className="eds-type-small">{msg}</p>
            <Button size="sm" disabled={!props.canIntel} onClick={() => void generate(offer)}>Сформировать сейчас</Button>
          </div>
        ) : null}
        {recalc ? (
          <div className="mt-2">
            <p className="eds-type-small">{msg || "Есть более свежие данные."}</p>
            <Button size="sm" disabled={!props.canIntel} onClick={() => { setRecalc(""); void generate(recalc, { recalculate: true }); }}>Пересчитать сейчас</Button>
          </div>
        ) : null}
        {msg && !offer && !recalc ? <p className="eds-type-small mt-2">{msg}</p> : null}
        {report ? (
          <div className="mt-3" data-testid="agro-intel-report">
            <div className="font-medium">
              {String(report.title)}{" "}
              <span className="eds-type-caption">{report.is_latest ? "АКТУАЛЬНЫЙ" : String(report.latest_badge_ru || "УСТАРЕЛ")}</span>
              {report.version ? <span className="eds-type-caption"> · v{String(report.version)}</span> : null}
            </div>
            <p className="eds-type-small text-[var(--ew-muted)]">{kyivSlice(report.generated_at_kyiv || report.generated_at)} · {String(report.timezone || "Europe/Kyiv")}</p>
            <p className="eds-type-small">{String(report.business_summary_ru || (!isTech(report.sources_note_ru) ? report.sources_note_ru : "Получены свежие данные по погоде, валюте, торговле и рынкам.") || report.summary || "")}</p>
            <p className="eds-type-caption">ID: {String(report.id || "")}</p>
            {Array.isArray(report.themes) && (report.themes as Row[])[0] ? (
              <p className="eds-type-small mt-2">{String(((report.themes as Row[])[0] || {}).detail_ru || "")}</p>
            ) : null}
            {(businessSections.length ? businessSections : sections).map((s) => (
              <div key={pick(s, "id")} className="mt-2 border-b border-[var(--ew-border)] pb-2">
                <div className="eds-type-small font-medium">{pick(s, "label_ru")}</div>
                {((s.compact as Row[]) || (s.bullets as Row[]) || []).length ? (
                  (((s.compact as Row[]) || (s.bullets as Row[])) as Row[]).slice(0, 3).map((b, i) => (
                    <div key={i} className="flex items-start justify-between gap-2 eds-type-small">
                      <span>
                        {b.marker ? <strong className="mr-1">{String(b.marker)}</strong> : null}
                        • {String(b.text || b.summary || "")}
                      </span>
                      <Button size="sm" variant="ghost" onClick={() => setDetail(b)}>
                        [Источники]
                      </Button>
                    </div>
                  ))
                ) : (
                  <p className="eds-type-small text-[var(--ew-muted)]">{String(s.note_ru || "Требуется подключение источника")}</p>
                )}
                <button type="button" className="eds-type-caption underline" onClick={() => setOpenBiz(openBiz === pick(s, "id") ? "" : pick(s, "id"))}>
                  Подробнее
                </button>
                {openBiz === pick(s, "id") && Array.isArray(s.full || s.bullets) ? (
                  <ul className="eds-type-small mt-1">
                    {((s.full as Row[]) || (s.bullets as Row[]) || []).map((b, i) => (
                      <li key={i}>{String((b as Row).text || (b as Row).summary || b)}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ))}
            {businessSections.length ? (
              <details className="mt-2">
                <summary className="eds-type-caption cursor-pointer">Подробнее · исходные блоки</summary>
                {sections.map((s) => (
                  <div key={`raw-${pick(s, "id")}`} className="mt-1 eds-type-small">
                    <div className="font-medium">{pick(s, "label_ru")}</div>
                    {Array.isArray(s.bullets) && s.bullets.length
                      ? (s.bullets as Row[]).map((b, i) => <div key={i}>• {String(b.text || b.summary || "")}</div>)
                      : <p>{String(s.note_ru || "Требуется подключение источника")}</p>}
                  </div>
                ))}
              </details>
            ) : null}
            <div className="mt-3 eds-type-small" data-testid="agro-intel-report-footer">
              <div>Источники: {String(report.sources_count ?? report.source_count ?? report.observation_count ?? 0)}</div>
              <div>Уверенность: {String(report.confidence ?? "—")}%</div>
              <div>
                Статус: {report.is_latest ? "АКТУАЛЬНЫЙ" : String(report.latest_badge_ru || "УСТАРЕЛ")}
              </div>
              <div>Пробелы данных: {Array.isArray(report.data_gaps) && (report.data_gaps as string[]).length ? (report.data_gaps as string[]).join("; ") : (Array.isArray(report.data_gaps_json) && (report.data_gaps_json as string[]).length ? (report.data_gaps_json as string[]).join("; ") : "нет")}</div>
              <details>
                <summary className="cursor-pointer eds-type-caption">Технические сведения</summary>
                <div>Версия конвейера: {String(report.pipeline_version || "—")}</div>
              </details>
            </div>
          </div>
        ) : null}
      </Card>

      <Card title="История обзоров">
        <div data-testid="agro-intel-history">
          {history.length === 0 ? <p className="eds-type-small text-[var(--ew-muted)]">Пока нет сохранённых обзоров.</p> : null}
          {history.map((h) => (
            <div key={pick(h, "id")} className="mb-2 flex items-center justify-between border-b border-[var(--ew-border)] pb-2">
              <div className="eds-type-small">
                <div>
                  {String(h.report_date || "").slice(0, 10)} · {String(h.title)} {h.is_latest ? "АКТУАЛЬНЫЙ" : String(h.latest_badge_ru || "УСТАРЕЛ")}
                </div>
                <div className="text-[var(--ew-muted)]">{kyivSlice(h.generated_at_kyiv || h.generated_at)} · уверенность {String(h.confidence ?? "—")}% · источников: {String(h.sources_count ?? 0)}</div>
              </div>
              <Button size="sm" variant="ghost" data-testid={`agro-intel-open-${pick(h, "id")}`} onClick={async () => {
                setReport(h);
                const r = await agroOpsGet(`/reports/${pick(h, "id")}`, props.headers);
                const item = (r.json as { item?: Row }).item;
                if (item) setReport(item);
              }}>Открыть</Button>
            </div>
          ))}
        </div>
      </Card>

      {detail ? (
        <Card title="Источники">
          <div className="eds-type-small" data-testid="agro-intel-detail">
            {((detail._all as Row[]) || [detail]).map((s, i) => (
              <div key={i} className="mb-2 border-b border-[var(--ew-border)] pb-2">
                <div>Провайдер: {String(s.provider_id || s.provider || s.source || "—")}</div>
                <div>Наблюдение: {String(s.title || s.text || s.observation_id || s.id || "—")}</div>
                <div>Дата: {String(s.date || s.published_at || s.observed_at || s.ingested_at || "—")}</div>
                <div>Значение: {String(s.value ?? s.normalized_value ?? "—")} {String(s.unit || "")}</div>
                <div>URL: {String(s.url || s.source_url || "—")}</div>
              </div>
            ))}
          </div>
          <div className="mt-2 flex gap-2">
            <Input value={ask} onChange={(e) => setAsk(e.target.value)} placeholder="Спросить помощника по этой карточке" />
            <Button
              size="sm"
              disabled={!props.canIntel || !ask.trim()}
              onClick={async () => {
                const r = await agroOpsPost("/ai/ask", { question: ask, context: detail }, props.headers);
                setAnswer((r.json as { item?: Row }).item || null);
              }}
            >
              Спросить помощника
            </Button>
          </div>
          {answer ? <p className="eds-type-small mt-2">{String(answer.answer_ru)}</p> : null}
          <Button className="mt-2" size="sm" variant="ghost" onClick={() => setDetail(null)}>Закрыть</Button>
        </Card>
      ) : null}

      <Card title="Добавить URL источника">
        <p className="eds-type-small mb-2">
          Система классифицирует URL (OFFICIAL_API / PUBLIC_DATA / RSS / MANUAL_SOURCE / UNKNOWN). UNKNOWN не входит в high-confidence анализ.
        </p>
        <Input className="mb-2" placeholder="https://…" value={customUrl} onChange={(e) => setCustomUrl(e.target.value)} />
        <div className="mb-2 flex flex-wrap gap-2 eds-type-small">
          {["HIGH", "MEDIUM", "LOW"].map((t) => (
            <Button key={t} size="sm" variant={customTrust === t ? "primary" : "ghost"} onClick={() => setCustomTrust(t)}>
              Доверие {t}
            </Button>
          ))}
        </div>
        <Button
          size="sm"
          disabled={!props.canIntel || !customUrl.trim()}
          onClick={async () => {
            const r = await agroOpsPost("/providers/custom", { url: customUrl, trust_level: customTrust }, props.headers);
            const j = r.json as { ok?: boolean; source_class?: string; message_ru?: string };
            setMsg(j.ok ? `Источник добавлен (${j.source_class || "UNKNOWN"})` : j.message_ru || "Не удалось добавить URL");
            setCustomUrl("");
            await reload();
          }}
        >
          Добавить URL
        </Button>
      </Card>

      <Card title="Расписание (Europe/Kyiv)">
        <p className="eds-type-small mb-2">Предложенные слоты. Можно изменить время в настройках.</p>
        <div className="eds-type-small" data-testid="agro-intel-scheduler">
          {(((schedule?.jobs_human as Row[]) || (schedule?.jobs as Row[]) || []) as Row[]).map((job) => (
            <div key={pick(job, "id")}>
              {String(job.time_kyiv || "")} {pick(job, "label_ru")}
            </div>
          ))}
          <details>
            <summary className="cursor-pointer">Расширенные настройки</summary>
            {(((schedule?.jobs as Row[]) || []) as Row[]).map((job) => (
              <div key={`cron-${pick(job, "id")}`}>
                {pick(job, "cron_kyiv")} · {pick(job, "label_ru")}
              </div>
            ))}
          </details>
          {!schedule?.jobs ? <p className="text-[var(--ew-muted)]">Загрузка расписания…</p> : null}
        </div>
      </Card>

      <Card title="Ручной импорт">
        <p className="eds-type-small mb-2">Добавьте сообщение из официального источника. Дубликаты отсекаются.</p>
        <Input className="mb-2" placeholder="Заголовок" value={importTitle} onChange={(e) => setImportTitle(e.target.value)} />
        <Input placeholder="Кратко / источник" value={importSummary} onChange={(e) => setImportSummary(e.target.value)} />
        <Button
          className="mt-2"
          size="sm"
          disabled={!props.canIntel || !importTitle.trim()}
          onClick={async () => {
            const r = await agroOpsPost("/intel/import", { title: importTitle, summary: importSummary, source: "manual_import" }, props.headers);
            const body = r.json as { ok?: boolean; message_ru?: string };
            setMsg(body.ok ? "Сообщение импортировано" : body.message_ru || "Ошибка импорта");
            setImportTitle("");
          }}
        >
          Импортировать
        </Button>
      </Card>

      <Card title="Агро-аналитики">
        <Button
          size="sm"
          disabled={!props.canIntel || Boolean(loading)}
          onClick={async () => {
            setLoading("agents");
            const r = await agroOpsPost("/agents/run", {}, props.headers);
            setLoading("");
            const item = (r.json as { item?: Row }).item || null;
            setAgents(item);
            setMsg(item ? "Аналитики сохранены" : "Не удалось запустить аналитиков");
          }}
        >
          Запустить аналитиков
        </Button>
        {agents ? (
          <div className="mt-2 eds-type-small" data-testid="agro-intel-agents">
            <div>Техническая информация. ID: {String(agents.id || "")}</div>
            <div>
              Главный вывод: {ru(BIAS_RU, String((agents.chief as Row | undefined)?.bias || "WATCH"))} · уверенность{" "}
              {String((agents.chief as Row | undefined)?.confidence ?? "")}
            </div>
            <div className="text-[var(--ew-muted)]">{String((agents.chief as Row | undefined)?.note_ru || "")}</div>
          </div>
        ) : null}
      </Card>
    </div>
  );
}
