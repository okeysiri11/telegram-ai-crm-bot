/**
 * AGRO 1.5 — analytics desk: conclusion, change, gaps, history, custom query.
 */

import { useEffect, useState, type ReactNode } from "react";
import { Button, Card, Input } from "@/ui";
import { agroOpsGet, agroOpsPost, pick } from "../business-ops/opsApi";
import { AgroCoverageCard } from "./AgroCoverageCard";
import { BIAS_RU, GAP_SEVERITY_RU, RISK_LEVEL_RU, ru } from "./agroLabels";

type Row = Record<string, unknown>;

const TYPES: { id: string; label: string }[] = [
  { id: "operational", label: "Оперативный анализ" },
  { id: "morning", label: "Утренний анализ" },
  { id: "evening", label: "Вечерний анализ" },
  { id: "weekly", label: "Недельный анализ" },
  { id: "outlook", label: "Стратегический прогноз 1–2 месяца" },
  { id: "custom", label: "Пользовательский анализ" },
];

function Sparkline(props: { label: string; points: Row[] }) {
  const pts = props.points
    .map((p) => Number(p.v))
    .filter((n) => Number.isFinite(n));
  const metric = String(props.points[0]?.metric || props.points[0]?.series_id || props.label);
  const unit = String(props.points[0]?.unit || "");
  if (pts.length < 2) {
    return (
      <div className="eds-type-small" data-testid={`agro-chart-${props.label}`} data-metric={metric} data-unit={unit}>
        {props.label}: {pts.length === 1 ? `${pts[0]} ${String(props.points[0]?.unit || "")}` : "нет числового ряда"}
      </div>
    );
  }
  const min = Math.min(...pts);
  const max = Math.max(...pts);
  const span = max - min || 1;
  const w = 220;
  const h = 48;
  const d = pts
    .map((v, i) => {
      const x = (i / (pts.length - 1)) * w;
      const y = h - ((v - min) / span) * (h - 4) - 2;
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  const last = props.points[props.points.length - 1];
  return (
    <div className="eds-type-small" data-testid={`agro-chart-${props.label}`} data-metric={metric} data-unit={unit}>
      <div className="mb-1 font-medium">
        {props.label}: {String(last?.v ?? "—")} {String(last?.unit || "")} · {String(last?.source || "")}
      </div>
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} role="img" aria-label={props.label}>
        <path d={d} fill="none" stroke="currentColor" strokeWidth="1.5" />
      </svg>
    </div>
  );
}

function cropHref(name: string): string {
  return `/workspace/agro?view=crops&crop=${encodeURIComponent(name)}`;
}

function CropLink({ text }: { text: string }) {
  const wheat = /пшениц/i.test(text);
  const corn = /кукуруз/i.test(text);
  if (wheat) {
    return (
      <a className="underline" href={cropHref("Пшеница")}>
        Пшеница
      </a>
    );
  }
  if (corn) {
    return (
      <a className="underline" href={cropHref("Кукуруза")}>
        Кукуруза
      </a>
    );
  }
  return null;
}

export function AgroAnalyticsPanel(props: { headers: Record<string, string>; canIntel: boolean }) {
  const [dash, setDash] = useState<Row | null>(null);
  const [history, setHistory] = useState<Row[]>([]);
  const [analysis, setAnalysis] = useState<Row | null>(null);
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [lineage, setLineage] = useState<Row[] | null>(null);
  const [tech, setTech] = useState(false);
  const [kind, setKind] = useState("operational");
  const [question, setQuestion] = useState("");
  const [crop, setCrop] = useState("");
  const [country, setCountry] = useState("");
  const [region, setRegion] = useState("");
  const [period, setPeriod] = useState("");
  const [source, setSource] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");

  async function reload(keep?: Row | null) {
    const d = await agroOpsGet("/analytics/dashboard", props.headers);
    setDash((d.json || {}) as Row);
    const h = await agroOpsGet("/analytics", props.headers);
    const items = ((h.json as { items?: Row[] })?.items || []) as Row[];
    setHistory(items);
    if (keep) setAnalysis(keep);
    else if (!analysis && items[0]) setAnalysis(items[0]);
  }

  useEffect(() => {
    void reload();
  }, [props.headers]);

  async function run(extra: Record<string, unknown> = {}) {
    setLoading("run");
    setError("");
    const body = {
      analysis_type: kind,
      question: kind === "custom" ? question : extra.question,
      crop: crop || undefined,
      country: country || undefined,
      region: region || undefined,
      period: period || undefined,
      source: source || undefined,
      ...extra,
    };
    const r = await agroOpsPost("/analytics/run", body, props.headers);
    const j = r.json as { ok?: boolean; item?: Row; message_ru?: string };
    setLoading("");
    if (!r.ok && !j.ok) {
      setError(j.message_ru || "Не удалось запустить анализ");
      return;
    }
    setAnalysis(j.item || null);
    setMsg("Анализ сохранён");
    await reload(j.item || null);
  }

  async function openId(id: string) {
    const r = await agroOpsGet(`/analytics/${id}`, props.headers);
    setAnalysis(((r.json as { item?: Row }).item || null) as Row | null);
  }

  const chief = (analysis?.chief as Row | undefined) || {};
  const sections = (analysis?.sections as Record<string, Row> | undefined) || {};
  const freshness = ((dash?.freshness as Row[]) || analysis?.freshness || []) as Row[];
  const gapsStructured = ((analysis?.data_gaps_structured as Row[]) || (dash?.gaps_structured as Row[]) || []) as Row[];
  const gaps = ((analysis?.data_gaps as string[]) || (dash?.gaps as string[]) || []) as string[];
  const series = ((analysis?.series as Record<string, Row[]>) || (dash?.series as Record<string, Row[]>) || {}) as Record<string, Row[]>;

  function openLineage(sources: unknown) {
    const rows = Array.isArray(sources) ? (sources as Row[]) : sources ? [sources as Row] : [];
    setLineage(rows.length ? rows : null);
  }

  function block(id: string, title: string, children: ReactNode) {
    return (
      <Card title={title}>
        <div data-testid={`agro-analytics-${id}`}>{children}</div>
      </Card>
    );
  }

  function category(secId: string, title: string) {
    const sec = sections[secId] || {};
    const bullets = (sec.bullets as Row[]) || [];
    return block(
      secId,
      title,
      bullets.length ? (
        <ul className="eds-type-small">
          {bullets.map((b, i) => (
            <li key={i}>
              {String(b.text || "")} {b.crop ? <CropLink text={String(b.crop)} /> : <CropLink text={String(b.text || "")} />}
              {b.metadata_only ? <span className="text-[var(--ew-muted)]"> · метаданные</span> : null}
            </li>
          ))}
          {sec.note_ru ? <li className="text-[var(--ew-muted)]">{String(sec.note_ru)}</li> : null}
        </ul>
      ) : (
        <p className="eds-type-small text-[var(--ew-muted)]">{String(sec.note_ru || "Недостаточно данных")}</p>
      ),
    );
  }

  return (
    <div className="grid gap-3 overflow-x-hidden max-w-[1920px]" data-testid="agro-analytics-panel">
      <Card title="Сводка">
        <p className="eds-type-small" data-testid="agro-analytics-brief">
          {String((dash?.business_brief as Row | undefined)?.text_ru || "Получены свежие данные по погоде, валюте, торговле и рынкам.")}
        </p>
      </Card>
      <Card title="ЧТО ИЗМЕНИЛОСЬ ЗА 24 ЧАСА">
        <ul className="eds-type-small" data-testid="agro-analytics-what-changed">
          {(((dash?.what_changed as Row[]) || analysis?.what_changed || []) as Row[]).length === 0 ? (
            <li>Существенных фактических изменений за 24 часа нет.</li>
          ) : (
            (((dash?.what_changed as Row[]) || analysis?.what_changed || []) as Row[]).map((c, i) => (
              <li key={i}>{String(c.text_ru || c.text || "")}</li>
            ))
          )}
        </ul>
      </Card>
      <Card title="РИСКИ СЕГОДНЯ">
        <div className="grid gap-2 sm:grid-cols-2" data-testid="agro-analytics-risk-cards">
          {(((dash?.risk_cards as Row[]) || []) as Row[]).map((c) => (
            <div key={String(c.title_ru)} className="rounded border border-[var(--ew-border)] p-2 eds-type-small">
              <div className="font-medium">{String(c.title_ru)} · {String(c.severity)}</div>
              <p>{String(c.summary_ru)}</p>
            </div>
          ))}
        </div>
      </Card>
      <Card title="ВОЗМОЖНОСТИ">
        <div data-testid="agro-analytics-opportunity-cards" className="eds-type-small">
          {(((dash?.opportunity_cards as Row[]) || []) as Row[]).map((c, i) => (
            <div key={i}>Потенциальная возможность · {String(c.commodity || "")} · {String(c.reason_ru || "")}</div>
          ))}
        </div>
      </Card>
      <details>
        <summary className="cursor-pointer eds-type-small">Подробнее</summary>
      <AgroCoverageCard coverage={(dash?.coverage as Record<string, number> | undefined) || dash || undefined} />
      <Card title="ЗДОРОВЬЕ ИСТОЧНИКОВ">
        <div className="eds-type-small grid gap-1" data-testid="agro-analytics-source-health">
          <div>Healthy: {Number((dash?.source_health as Row | undefined)?.healthy || 0)}</div>
          <div>Partial: {Number((dash?.source_health as Row | undefined)?.partial || 0)}</div>
          <div>Needs key: {Number((dash?.source_health as Row | undefined)?.needs_key || 0)}</div>
          <div>Optional: {Number((dash?.source_health as Row | undefined)?.optional || 0)}</div>
          <div>Failed: {Number((dash?.source_health as Row | undefined)?.failed || 0)}</div>
          <div>Last full refresh: {String((dash?.source_health as Row | undefined)?.last_full_refresh_at || "—")}</div>
          <div>Refresh duration: {String((dash?.source_health as Row | undefined)?.refresh_duration_sec ?? "—")} sec</div>
        </div>
      </Card>
      <Card title="Операционные счётчики">
        <div className="eds-type-small grid gap-1" data-testid="agro-analytics-operational-counts">
          <div>Числовых наблюдений: {Number((dash?.operational_counts as Row | undefined)?.numeric_observations || 0)}</div>
          <div>Свежих &lt;24ч: {Number((dash?.operational_counts as Row | undefined)?.fresh_24h || 0)}</div>
          <div>За 7 дней: {Number((dash?.operational_counts as Row | undefined)?.last_7d || 0)}</div>
          <div>Исторических: {Number((dash?.operational_counts as Row | undefined)?.historical || 0)}</div>
          <div>Ценовых: {Number((dash?.operational_counts as Row | undefined)?.price || 0)}</div>
          <div>Погодных: {Number((dash?.operational_counts as Row | undefined)?.weather || 0)}</div>
          <div>Торговых: {Number((dash?.operational_counts as Row | undefined)?.trade || 0)}</div>
          <div>Логистических: {Number((dash?.operational_counts as Row | undefined)?.logistics || 0)}</div>
        </div>
      </Card>
      <Card title="СВЕЖЕСТЬ ДАННЫХ">
        <div data-testid="agro-analytics-freshness" className="eds-type-small grid gap-1">
          {freshness.length === 0 ? <p className="text-[var(--ew-muted)]">Опросите источники в Агро-разведке.</p> : null}
          {freshness.map((f) => (
            <div key={pick(f, "provider_id")}>
              {pick(f, "label_ru")}: {pick(f, "age_ru")}
              {f.live ? "" : ""}
            </div>
          ))}
        </div>
      </Card>

      <Card title="РЯДЫ (ЧИСЛОВЫЕ)">
        <div className="grid gap-2 sm:grid-cols-2" data-testid="agro-analytics-charts">
          <Sparkline label="price" points={series.price || []} />
          <Sparkline label="production" points={series.production || []} />
          <Sparkline label="yield_or_area" points={series.yield_or_area || []} />
          <Sparkline label="trade" points={series.trade || []} />
          <Sparkline label="fx" points={series.fx || []} />
          <Sparkline label="weather" points={series.weather || []} />
        </div>
      </Card>

      <Card title="ПРОБЕЛЫ ДАННЫХ">
        <ul className="eds-type-small" data-testid="agro-analytics-gaps">
          {gapsStructured.length
            ? gapsStructured.map((g) => (
                <li key={String(g.code || g.text)}>
                  <strong>{GAP_SEVERITY_RU[String(g.severity)] || String(g.severity)}</strong> ⚠ {String(g.text)}
                </li>
              ))
            : gaps.length === 0
              ? <li>Явных пробелов не зафиксировано.</li>
              : gaps.map((g) => <li key={g}>⚠ {g}</li>)}
        </ul>
      </Card>

      <Card title="Проверка качества / аномалии">
        <ul className="eds-type-small" data-testid="agro-analytics-quality">
          {(((analysis?.quality_flags as Row[]) || (dash?.quality_flags as Row[]) || []) as Row[]).length === 0 ? (
            <li>Подозрительных записей нет.</li>
          ) : (
            (((analysis?.quality_flags as Row[]) || (dash?.quality_flags as Row[]) || []) as Row[]).map((f, i) => (
              <li key={i}>{String(f.code)}: {String(f.text)} {f.kept ? "(сохранено)" : ""}</li>
            ))
          )}
        </ul>
        <ul className="eds-type-small mt-2" data-testid="agro-analytics-anomalies">
          {(((analysis?.anomalies as Row[]) || (dash?.anomalies as Row[]) || []) as Row[]).map((a, i) => (
            <li key={i}>{String(a.text)}</li>
          ))}
        </ul>
      </Card>
      </details>

      <Card title="Запуск анализа">
        <div className="mb-2 flex flex-wrap gap-2">
          {TYPES.map((t) => (
            <Button key={t.id} size="sm" variant={kind === t.id ? "primary" : "ghost"} onClick={() => setKind(t.id)}>
              {t.label}
            </Button>
          ))}
        </div>
        {kind === "custom" ? (
          <div className="mb-2 grid gap-2" data-testid="agro-analytics-custom">
            <p className="eds-type-small font-medium">СВОЙ ЗАПРОС</p>
            <Input
              placeholder="Что вы хотите проанализировать?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
            <div className="grid gap-2 sm:grid-cols-2">
              <Input placeholder="Культура" value={crop} onChange={(e) => setCrop(e.target.value)} />
              <Input placeholder="Страна" value={country} onChange={(e) => setCountry(e.target.value)} />
              <Input placeholder="Регион" value={region} onChange={(e) => setRegion(e.target.value)} />
              <Input placeholder="Период (YYYY-MM-DD)" value={period} onChange={(e) => setPeriod(e.target.value)} />
              <Input placeholder="Источник" value={source} onChange={(e) => setSource(e.target.value)} />
            </div>
          </div>
        ) : null}
        <Button size="sm" disabled={!props.canIntel || Boolean(loading)} onClick={() => void run()}>
          ЗАПУСТИТЬ АНАЛИЗ
        </Button>
        <Button className="ml-2" size="sm" variant="ghost" disabled={!props.canIntel || Boolean(loading)} onClick={() => void run()}>
          Пересчитать анализ
        </Button>
        {kind === "custom" ? (
          <Button className="ml-2" size="sm" disabled={!props.canIntel || !question.trim()} onClick={() => void run()}>
            Анализировать
          </Button>
        ) : null}
        {loading ? <span className="eds-type-small ml-2">Загрузка…</span> : null}
        {error ? <p className="eds-type-small text-[var(--ew-danger)]">{error}</p> : null}
        {msg ? <p className="eds-type-small mt-1">{msg}</p> : null}
      </Card>

      {analysis ? (
        <>
          {block(
            "chief",
            "Главное заключение",
            <div>
              <div className="font-medium">
                {String(analysis.title_ru || analysis.title)} · {ru(BIAS_RU, String(analysis.bias || chief.bias || "WATCH"))} ·{" "}
                {String(analysis.confidence ?? chief.confidence ?? "—")}%
              </div>
              <p className="eds-type-small text-[var(--ew-muted)]">
                {String(analysis.generated_at_human || analysis.generated_at_kyiv || "")} · {String(analysis.topic_ru || "")}
              </p>
              <p className="eds-type-small mt-1">{String(chief.note_ru || chief.conclusion_ru || "")}</p>
              <Button size="sm" variant="ghost" onClick={() => openLineage(chief.observations || analysis?.sources)}>
                [Источники]
              </Button>
              <p className="eds-type-small mt-1">Ключевые факторы: {((analysis.key_factors as string[]) || []).join("; ") || "—"}</p>
            </div>,
          )}
          {block(
            "changed",
            "Что изменилось",
            ((analysis.what_changed as Row[]) || []).length ? (
              <ul className="eds-type-small">
                {((analysis.what_changed as Row[]) || []).map((c, i) => (
                  <li key={i}>
                    <strong>{String(c.marker)}</strong> {String(c.text)}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="eds-type-small text-[var(--ew-muted)]">Нет предыдущего запуска для сравнения.</p>
            ),
          )}
          {block(
            "risks",
            "Риски",
            ((analysis.risks as Row[]) || []).length ? (
              <ul className="eds-type-small">
                {((analysis.risks as Row[]) || []).map((r, i) => (
                  <li key={i}>
                    {r.level ? <strong className="mr-1">{RISK_LEVEL_RU[String(r.level)] || String(r.level)}</strong> : null}
                    {String(r.text)}
                    {r.reason ? <span className="text-[var(--ew-muted)]"> · {String(r.reason)}</span> : null}
                    <Button className="ml-2" size="sm" variant="ghost" onClick={() => openLineage(r.sources)}>
                      [Источники]
                    </Button>
                    <Button
                      className="ml-2"
                      size="sm"
                      variant="ghost"
                      disabled={!props.canIntel}
                      onClick={async () => {
                        await agroOpsPost(`/analytics/${analysis.id}/notify`, { title: `Уведомить: ${r.text}`, trigger: "risk_high" }, props.headers);
                        setMsg("Уведомление создано");
                      }}
                    >
                      Создать уведомление
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={!props.canIntel}
                      onClick={async () => {
                        await agroOpsPost(
                          `/analytics/${analysis.id}/task`,
                          { title: String(r.text), analysis_id: analysis.id, commodity: analysis.topic_ru, priority: "high" },
                          props.headers,
                        );
                        setMsg("Задача создана");
                      }}
                    >
                      Создать задачу
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={!props.canIntel}
                      onClick={async () => {
                        await agroOpsPost(`/analytics/${analysis.id}/calendar`, { title: String(r.text) }, props.headers);
                        setMsg("Событие добавлено в календарь");
                      }}
                    >
                      Добавить в календарь
                    </Button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="eds-type-small text-[var(--ew-muted)]">Недостаточно данных</p>
            ),
          )}
          {block(
            "opportunities",
            "Возможности",
            ((analysis.opportunities as Row[]) || []).length ? (
              <ul className="eds-type-small">
                {((analysis.opportunities as Row[]) || []).map((o, i) => (
                  <li key={i}>
                    <div className="font-medium">{String(o.label_ru || "Потенциальная возможность")}</div>
                    <div>{String(o.text)}</div>
                    {o.commodity ? (
                      <div className="text-[var(--ew-muted)]">
                        {String(o.commodity)} · {String(o.buy_market || "—")} → {String(o.sell_market || "—")} · спред {String(o.price_difference ?? "—")} · логистика {String(o.estimated_logistics_note || o.estimated_logistics || "Нет актуальной коммерческой ставки")} · FX {JSON.stringify(o.fx || [])} · gross {String(o.gross_spread ?? "—")} · уверенность {String(o.data_confidence || "—")}
                      </div>
                    ) : null}
                    <Button className="ml-2" size="sm" variant="ghost" onClick={() => openLineage(o.sources)}>
                      [Источники]
                    </Button>
                    <Button className="ml-2" size="sm" variant="ghost" disabled={!props.canIntel} onClick={async () => {
                      await agroOpsPost(`/analytics/${analysis.id}/task`, { title: String(o.text), analysis_id: analysis.id }, props.headers);
                      setMsg("Задача создана");
                    }}>Создать задачу</Button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="eds-type-small text-[var(--ew-muted)]">Недостаточно данных</p>
            ),
          )}
          {category("ukraine", "Украина")}
          {category("prices", "Цены")}
          {category("harvest", "Урожай")}
          {category("trade", "Экспорт")}
          {category("weather", "Погода")}
          {category("logistics", "Логистика")}
          {category("world", "Мировые рынки")}
          {block(
            "consensus",
            "Консенсус аналитиков",
            <ul className="eds-type-small">
              {((analysis.consensus as Row[]) || []).map((c) => (
                <li key={pick(c, "agent")}>
                  {pick(c, "label_ru")}: {String(c.conclusion || "Недостаточно данных")}
                </li>
              ))}
            </ul>,
          )}
          {block(
            "sources",
            "Источники",
            <div>
              <Button size="sm" variant="ghost" onClick={() => setSourcesOpen((v) => !v)}>
                Показать источники
              </Button>
              {sourcesOpen ? (
                <ul className="eds-type-small mt-2" data-testid="agro-analytics-source-records">
                  {((analysis.sources as Row[]) || []).map((s) => (
                    <li key={pick(s, "provider_id")}>
                      {pick(s, "label_ru")}
                      <ul>
                        {((s.records as Row[]) || []).map((rec) => (
                          <li key={pick(rec, "id")}>{String(rec.text || rec.title || "")}</li>
                        ))}
                      </ul>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>,
          )}
          {block(
            "gaps-detail",
            "Пробелы данных",
            <ul className="eds-type-small">
              {gaps.map((g) => (
                <li key={g}>⚠ {g}</li>
              ))}
            </ul>,
          )}
          <p className="eds-type-caption">
            <button type="button" className="underline" onClick={() => setTech((v) => !v)}>
              Техническая информация
            </button>
            {tech ? <span> · {String(analysis.id)}</span> : null}
          </p>
        </>
      ) : null}

      <Card title="ИСТОРИЯ АНАЛИЗОВ">
        <div data-testid="agro-analytics-history">
          {history.length === 0 ? <p className="eds-type-small text-[var(--ew-muted)]">Пока нет сохранённых анализов.</p> : null}
          {history.map((h) => (
            <div key={pick(h, "id")} className="mb-2 flex items-center justify-between border-b border-[var(--ew-border)] pb-2">
              <div className="eds-type-small">
                <div>
                  {String(h.generated_at_human || "").slice(0, 32)} · {TYPES.find((t) => t.id === h.analysis_type)?.label || String(h.analysis_type)}
                </div>
                <div className="text-[var(--ew-muted)]">
                  {String(h.topic_ru || "Общий рынок")} · {ru(BIAS_RU, String(h.bias || "WATCH"))} · {String(h.confidence ?? "—")}% ·{" "}
                  {String(h.sources_count ?? 0)} источников
                </div>
              </div>
              <Button size="sm" variant="ghost" data-testid={`agro-analytics-open-${pick(h, "id")}`} onClick={() => void openId(pick(h, "id"))}>
                Открыть
              </Button>
            </div>
          ))}
        </div>
      </Card>

      {lineage ? (
        <Card title="Источники">
          <div className="eds-type-small" data-testid="agro-analytics-lineage">
            {lineage.map((s, i) => (
              <div key={i} className="mb-2 border-b border-[var(--ew-border)] pb-2">
                <div>Провайдер: {String(s.provider_id || s.provider || s.source || "—")}</div>
                <div>Наблюдение: {String(s.title || s.text || s.observation_id || s.id || "—")}</div>
                <div>Дата: {String(s.date || s.published_at || s.observed_at || "—")}</div>
                <div>Значение: {String(s.value ?? s.normalized_value ?? "—")} {String(s.unit || "")}</div>
                <div>URL: {String(s.url || s.source_url || "—")}</div>
              </div>
            ))}
          </div>
          <Button className="mt-2" size="sm" variant="ghost" onClick={() => setLineage(null)}>
            Закрыть
          </Button>
        </Card>
      ) : null}
    </div>
  );
}
