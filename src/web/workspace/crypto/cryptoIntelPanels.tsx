import { Link } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";

export function ConsensusVotePanel({
  votes,
  consensus,
}: {
  votes: Array<{ agent_name?: string; agent_id?: string; vote?: string; confidence?: number }>;
  consensus?: Record<string, unknown> | null;
}) {
  if (!consensus && (!votes || votes.length === 0)) {
    return <p className="eds-type-small text-[var(--eds-text-muted)]">Нет сохранённого консенсуса</p>;
  }
  const disagreement = Number(consensus?.disagreement_score ?? 0);
  const disagreementRu = disagreement < 0.34 ? "низкое" : disagreement < 0.67 ? "среднее" : "высокое";
  const finalBias = String(consensus?.final_result || consensus?.bias || consensus?.overall_direction || "—");
  return (
    <div data-testid="consensus-panel">
      <Card title="Консенсус Chief Analyst">
        <div className="space-y-1 eds-type-small font-mono">
          {votes.map((v) => (
            <div key={String(v.agent_id || v.agent_name)} className="flex justify-between gap-2">
              <span>{v.agent_name || v.agent_id}</span>
              <span>
                {String(v.vote || "—")}{" "}
                {v.confidence != null ? Math.round(Number(v.confidence) * 100) : "—"}
              </span>
            </div>
          ))}
        </div>
        <div className="mt-3 border-t border-[var(--eds-border)] pt-2">
          <p className="eds-type-body">
            Итог: <strong>{finalBias}</strong>
          </p>
          <p className="eds-type-small">
            Уверенность:{" "}
            {consensus?.overall_confidence != null || consensus?.confidence != null
              ? `${Math.round(Number(consensus?.overall_confidence ?? consensus?.confidence) * 100)}%`
              : "—"}
          </p>
          <p className="eds-type-small">
            Bullish {String(consensus?.bullish_score ?? "—")} · Bearish {String(consensus?.bearish_score ?? "—")} · Neutral{" "}
            {String(consensus?.neutral_score ?? "—")}
          </p>
          <p className="eds-type-caption text-[var(--eds-text-muted)]">Разногласие агентов: {disagreementRu}</p>
        </div>
      </Card>
    </div>
  );
}

export function AnalysisResultPanel({
  display,
  onCreateSignal,
}: {
  display: Record<string, unknown> | null;
  onCreateSignal?: () => void;
}) {
  if (!display) return null;
  const tech = (display.technical_factor || {}) as Record<string, unknown>;
  const bb = (tech.bollinger || {}) as Record<string, unknown>;
  const dxy = (display.dxy_state || display.dxy_factor || {}) as Record<string, unknown>;
  const macro = (display.macro_factor || {}) as Record<string, unknown>;
  const news = (display.news_factor || {}) as Record<string, unknown>;
  const corr = (display.correlation_factor || {}) as Record<string, unknown>;
  const risk = (display.risk_factor || {}) as Record<string, unknown>;
  const session = (display.session_factor || {}) as Record<string, unknown>;
  const eurusd = (display.eurusd_state || {}) as Record<string, unknown>;
  const gaps = (display.data_gaps as string[] | undefined) || (display.missing_sources as string[] | undefined) || [];
  const reasons = (display.key_reasons as string[] | undefined) || [];
  const changed = (display.what_changed as string[] | undefined) || [];
  const sources = (display.sources || {}) as Record<string, unknown>;
  const finalResult = String(display.final_result || display.direction || "—");

  return (
    <div className="space-y-3" data-testid="analysis-result">
      <Card title="Общий вывод">
        <p className="eds-type-body">
          <strong>{String(display.direction_ru || display.overall_summary || finalResult)}</strong> ({finalResult})
        </p>
        <p className="eds-type-small">Уверенность: {String(display.confidence_pct ?? "—")}%</p>
        <p className="eds-type-small">
          Bullish {String(display.bullish_score ?? "—")} · Bearish {String(display.bearish_score ?? "—")} · Neutral{" "}
          {String(display.neutral_score ?? "—")}
        </p>
        <p className="eds-type-caption text-[var(--eds-text-muted)]">Сгенерировано: {String(display.generated_at || "—")}</p>
      </Card>

      <Card title="EUR/USD состояние">
        <p className="eds-type-small">Котировка: {String((eurusd.mid as unknown) ?? (eurusd.quote as Record<string, unknown> | undefined)?.mid ?? "—")}</p>
        <p className="eds-type-small">Trend: {String((eurusd.technical as Record<string, unknown> | undefined)?.trend ?? tech.trend ?? "—")}</p>
        <p className="eds-type-small">Поддержка / сопротивление: {String(display.support ?? "—")} / {String(display.resistance ?? "—")}</p>
      </Card>

      <Card title="DXY состояние">
        <p className="eds-type-small">Голос: {String(dxy.vote ?? "—")}</p>
        <p className="eds-type-small">Котировка: {String(dxy.mid ?? (dxy.quote as Record<string, unknown> | undefined)?.mid ?? "—")}</p>
        <p className="eds-type-small">Trend: {String((dxy.technical as Record<string, unknown> | undefined)?.trend ?? "—")}</p>
      </Card>

      <Card title="Технический анализ">
        <div className="grid gap-1 sm:grid-cols-2 eds-type-small">
          <span>Trend: {String(tech.trend ?? "—")}</span>
          <span>EMA: {String(tech.ema_fast ?? "—")} / {String(tech.ema_slow ?? "—")}</span>
          <span>RSI: {String(tech.rsi ?? "—")}</span>
          <span>MACD: {String(tech.macd ?? "—")}</span>
          <span>ATR: {String(tech.atr ?? "—")}</span>
          <span>Bollinger: {String(bb.lower ?? "—")} · {String(bb.mid ?? "—")} · {String(bb.upper ?? "—")}</span>
          <span>SMA / EMA: {String(tech.ema_slow ?? "—")} / {String(tech.ema_fast ?? "—")}</span>
        </div>
      </Card>

      <Card title="Макро">
        <p className="eds-type-small">Голос: {String(macro.vote ?? "—")}</p>
        <p className="eds-type-small">Событий: {String(macro.events_count ?? "—")}</p>
        <p className="eds-type-caption">{((macro.risks as string[] | undefined) || []).join("; ") || "—"}</p>
      </Card>

      <Card title="Новости">
        <p className="eds-type-small">Голос: {String(news.vote ?? "—")}</p>
        <p className="eds-type-small">Материалов: {String(news.items_count ?? "—")}</p>
        <p className="eds-type-caption">{((news.notes as string[] | undefined) || []).join("; ") || "—"}</p>
      </Card>

      <Card title="Корреляция">
        <p className="eds-type-small">EUR/USD ↔ DXY: {String(corr.correlation ?? corr.value ?? "—")}</p>
        <p className="eds-type-caption">{String(corr.message || corr.status || "")}</p>
      </Card>

      <Card title="Риск">
        <p className="eds-type-small">Risk Agent: {String(risk.vote ?? "—")}</p>
        <p className="eds-type-small">{String(risk.note ?? "—")}</p>
      </Card>

      <Card title="Сессия">
        <p className="eds-type-small">Session Agent: {String(session.vote ?? "—")}</p>
        <p className="eds-type-small">Европа: {String(session.europe ?? "—")} · США: {String(session.us ?? "—")}</p>
      </Card>

      <Card title="Ключевые причины">
        {reasons.length ? (
          <ul className="list-disc pl-5 eds-type-small">
            {reasons.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        ) : (
          <p className="eds-type-small text-[var(--eds-text-muted)]">Нет данных</p>
        )}
      </Card>

      <Card title="Что изменилось">
        {changed.length ? (
          <ul className="list-disc pl-5 eds-type-small">
            {changed.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        ) : (
          <p className="eds-type-small text-[var(--eds-text-muted)]">Нет данных</p>
        )}
      </Card>

      <Card title="Data gaps">
        {gaps.length ? (
          <p className="eds-type-caption text-[var(--eds-warning,#b45309)]">{gaps.join("; ")}</p>
        ) : (
          <p className="eds-type-small">Пропусков источников нет</p>
        )}
        <p className="eds-type-caption text-[var(--eds-text-muted)] mt-2">
          Источники: EUR/USD={String(sources.eurusd || "—")}; DXY={String(sources.dxy || "—")}; bars=
          {String(sources.bars || "—")}; news={String(sources.news || "—")}; macro={String(sources.macro || "—")}
        </p>
      </Card>

      <ConsensusVotePanel
        votes={(display.agent_votes_panel as Array<Record<string, unknown>>) || []}
        consensus={(display.consensus as Record<string, unknown>) || null}
      />

      <div className="flex flex-wrap gap-2" data-testid="analysis-result-actions">
        <Button size="sm" className="ews-primary-cta" onClick={() => onCreateSignal?.()}>
          Создать сигнал
        </Button>
        <Link to="/workspace/crypto?view=paper">
          <Button size="sm" className="ews-primary-cta">
            Открыть бумажную сделку
          </Button>
        </Link>
        <Link to="/workspace/crypto?view=intel_history">
          <Button size="sm" className="ews-primary-cta">
            Открыть историю
          </Button>
        </Link>
      </div>
      <p className="eds-type-caption text-[var(--eds-text-muted)]">AI-анализ, не является гарантией результата.</p>
    </div>
  );
}

export function TechnicalSummaryCards({
  eurusd,
  dxy,
  timeframe,
  onTimeframe,
}: {
  eurusd: Record<string, unknown> | null;
  dxy: Record<string, unknown> | null;
  timeframe: string;
  onTimeframe: (tf: string) => void;
}) {
  const tfs = ["15m", "1H", "4H", "1D"];
  const row = (title: string, ind: Record<string, unknown> | null) => (
    <Card title={title}>
      {!ind || ind.status === "insufficient_data" ? (
        <p className="eds-type-small text-[var(--eds-text-muted)]">{String(ind?.message || "Нет данных")}</p>
      ) : (
        <div className="grid gap-1 sm:grid-cols-2 eds-type-small">
          <span>Trend: {String(ind.trend ?? "—")}</span>
          <span>EMA: {String(ind.ema_fast ?? "—")} / {String(ind.ema_slow ?? "—")}</span>
          <span>RSI: {String(ind.rsi ?? "—")}</span>
          <span>MACD: {String(ind.macd ?? "—")}</span>
          {title.startsWith("EUR") ? <span>ATR: {String(ind.atr ?? "—")}</span> : null}
          {title.startsWith("EUR") ? (
            <span>
              Bollinger: {String((ind.bollinger as Record<string, unknown> | undefined)?.mid ?? "—")}
            </span>
          ) : null}
          <span>Support: {String(ind.support ?? "—")}</span>
          <span>Resistance: {String(ind.resistance ?? "—")}</span>
        </div>
      )}
    </Card>
  );
  return (
    <div className="space-y-3" data-testid="ta-summary">
      <div className="flex flex-wrap gap-2">
        {tfs.map((tf) => (
          <Button key={tf} size="sm" variant={timeframe === tf ? undefined : "secondary"} className={timeframe === tf ? "ews-primary-cta" : ""} onClick={() => onTimeframe(tf)}>
            {tf}
          </Button>
        ))}
      </div>
      {row("EUR/USD", eurusd)}
      {row("DXY", dxy)}
    </div>
  );
}

export function NewsFeedPanel({
  items,
  filter,
  onFilter,
  loading,
}: {
  items: Record<string, unknown>[];
  filter: string;
  onFilter: (f: string) => void;
  loading?: boolean;
}) {
  const filters = ["Все", "EUR", "USD", "EUR/USD", "DXY", "Fed", "ECB", "Макро"];
  return (
    <div className="space-y-3" data-testid="news-feed">
      <div className="flex flex-wrap gap-2">
        {filters.map((f) => (
          <Button key={f} size="sm" variant={filter === f ? undefined : "secondary"} className={filter === f ? "ews-primary-cta" : ""} onClick={() => onFilter(f)}>
            {f}
          </Button>
        ))}
      </div>
      {loading ? <p className="eds-type-small">Загрузка…</p> : null}
      {!loading && items.length === 0 ? (
        <p className="eds-type-small text-[var(--eds-text-muted)]">Новостей пока нет по выбранному фильтру.</p>
      ) : null}
      {items.map((a) => (
        <Card key={String(a.id || a.duplicate_group_id || a.title)} title={String(a.title || "—")}>
          <div className="flex flex-wrap gap-2 eds-type-caption text-[var(--eds-text-muted)]">
            <span>{String(a.published_at || a.fetched_at || "—")}</span>
            <Badge>{String(a.source || "—")}</Badge>
            <span>{String(a.ai_assessment || a.sentiment || "Недостаточно данных")}</span>
            <span>{(a.instruments as string[] | undefined)?.join(", ") || "—"}</span>
          </div>
          {a.url ? (
            <a className="eds-type-small text-[var(--eds-accent)] underline" href={String(a.url)} target="_blank" rel="noreferrer">
              Открыть источник
            </a>
          ) : null}
        </Card>
      ))}
    </div>
  );
}

export function MacroCalendarPanel({ events }: { events: Record<string, unknown>[] }) {
  if (!events.length) {
    return <p className="eds-type-small text-[var(--eds-text-muted)]">Макрособытий пока нет или календарь недоступен.</p>;
  }
  return (
    <div className="space-y-2" data-testid="macro-calendar">
      {events.map((e) => (
        <Card key={String(e.external_key || e.id || `${e.event}-${e.scheduled_at}`)} title={String(e.title || e.event || "Событие")}>
          <p className="eds-type-small">
            {String(e.country || e.region || "—")} · {String(e.scheduled_at || "—")} · {String(e.importance || "—")}
          </p>
          <div className="mt-2 flex flex-wrap gap-2 eds-type-small">
            <Link className="underline" to="/workspace/crypto?view=analysis">Анализ</Link>
            <Link className="underline" to="/workspace/crypto?view=signals">Сигнал</Link>
            <Link className="underline" to="/workspace/crypto?view=paper">Бумажная сделка</Link>
          </div>
        </Card>
      ))}
    </div>
  );
}
