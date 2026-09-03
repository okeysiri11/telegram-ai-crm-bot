/**
 * Sprint 50.3 — dual charts, paper demo account, journal, notifications, cross-links.
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Button, Card, Input } from "@/ui";
import { DxyNativeChart } from "./DxyNativeChart";
import { EurUsdNativeChart } from "./EurUsdNativeChart";
import type { ChartTimeframe } from "./chartProvider";
import { formatFxQuote } from "./fxQuoteDisplay";

export { formatFxQuote, fxWatchlistQuoteRow } from "./fxQuoteDisplay";

export function integrityLabel(status?: string, mid?: unknown) {
  const hasMid = formatFxQuote(mid) != null;
  if (status === "connected" || status === "live" || status === "delayed") {
    return hasMid ? null : "Нет данных";
  }
  if (status === "error") return hasMid ? "Источник временно ограничил запросы" : "Источник недоступен";
  if (status === "needs_config" || status === "not_connected") return "Источник недоступен";
  if (status === "insufficient_data") return "Данные неполные";
  if (status === "stale" || status === "cached") return "Данные устарели";
  if (status === "partial") return "Частичные данные";
  if (!hasMid && status) return "Нет данных";
  if (!hasMid && !status) return "Нет данных";
  return null;
}

export function eurusdSourceLabel(quote: Record<string, unknown>): string {
  const source = String(quote.source || "");
  const provider = String(quote.provider || "");
  if (provider === "yahoo_eurusd" || source.includes("Yahoo") || source.includes("EURUSD=X")) {
    return source.includes("Yahoo") ? source : "Yahoo Finance (EURUSD=X)";
  }
  if (source && !/нбу|nbu/i.test(source)) return source;
  if (provider && provider !== "nbu_cross") return provider;
  return "Yahoo Finance (EURUSD=X)";
}

export function DualChartsPanel({
  eurusdTf,
  dxyTf,
  onEurusdTf,
  onDxyTf,
  timeframes,
  eurusdQuote,
  dxyQuote,
  onCreateSignal,
  layout = "vertical",
}: {
  eurusdTf: ChartTimeframe;
  dxyTf: ChartTimeframe;
  onEurusdTf: (tf: ChartTimeframe) => void;
  onDxyTf: (tf: ChartTimeframe) => void;
  timeframes: readonly ChartTimeframe[];
  eurusdQuote: Record<string, unknown>;
  dxyQuote: Record<string, unknown>;
  onCreateSignal: (instrument: string) => void;
  layout?: "vertical" | "horizontal";
}) {
  const grid = layout === "vertical" ? "grid gap-3" : "grid gap-3 lg:grid-cols-2";
  const chartH = layout === "vertical" ? 360 : 320;
  return (
    <div className="space-y-3" data-testid="dual-charts" data-layout={layout}>
      <div className={grid}>
        <Card title="EUR/USD">
          <div className="mb-2 flex flex-wrap gap-2" data-testid="tf-EUR/USD">
            {timeframes.map((t) => (
              <Button
                key={t}
                size="sm"
                variant={t === eurusdTf ? "primary" : "secondary"}
                onClick={() => onEurusdTf(t)}
                data-testid={`eurusd-tf-${t}`}
              >
                {t}
              </Button>
            ))}
          </div>
          <p
            className="eds-type-small"
            data-testid="eurusd-quote-line"
            data-fetched-at={String(eurusdQuote.fetched_at || "")}
            data-provider={String(eurusdQuote.provider || eurusdQuote.source || "")}
          >
            Котировка: {formatFxQuote(eurusdQuote.mid, 5) ?? "Нет данных"}
            {eurusdQuote.fetched_at ? ` · ${String(eurusdQuote.fetched_at)}` : ""}
            {` · ${eurusdSourceLabel(eurusdQuote)}`}
          </p>
          {integrityLabel(String(eurusdQuote.status || ""), eurusdQuote.mid) ? (
            <p className="eds-type-caption text-[var(--eds-warning,#b45309)]">
              {integrityLabel(String(eurusdQuote.status || ""), eurusdQuote.mid)}
            </p>
          ) : null}
          <EurUsdNativeChart symbol="EUR/USD" timeframe={eurusdTf} height={chartH} liveQuote={eurusdQuote} />
          <div className="mt-2 flex flex-wrap gap-2">
            <Button size="sm" className="ews-primary-cta" onClick={() => onCreateSignal("EUR/USD")} data-testid="chart-signal-EUR/USD">
              Создать сигнал
            </Button>
            <Link to="/workspace/crypto?view=analysis" data-testid="chart-analysis-EUR/USD">
              <Button size="sm" className="ews-primary-cta">
                К анализу
              </Button>
            </Link>
            <Link to="/workspace/crypto?view=paper" data-testid="chart-paper-EUR/USD">
              <Button size="sm" className="ews-primary-cta">
                Бумажная торговля
              </Button>
            </Link>
          </div>
        </Card>

        <Card title="DXY">
          <div className="mb-2 flex flex-wrap gap-2" data-testid="tf-DXY">
            {timeframes.map((t) => (
              <Button key={t} size="sm" variant={t === dxyTf ? "primary" : "secondary"} onClick={() => onDxyTf(t)} data-testid={`dxy-tf-${t}`}>
                {t}
              </Button>
            ))}
          </div>
          <p
            className="eds-type-small"
            data-testid="dxy-quote-line"
            data-fetched-at={String(dxyQuote.fetched_at || "")}
            data-provider={String(dxyQuote.provider || dxyQuote.source || "")}
          >
            Котировка: {formatFxQuote(dxyQuote.mid, 3) ?? "Нет данных"}
            {dxyQuote.fetched_at ? ` · ${String(dxyQuote.fetched_at)}` : ""}
            {dxyQuote.provider || dxyQuote.source ? ` · ${String(dxyQuote.provider || dxyQuote.source)}` : ""}
            {dxyQuote.freshness === "cached" || String(dxyQuote.freshness || "").includes("stale") ? " · Данные устарели" : ""}
          </p>
          {integrityLabel(String(dxyQuote.status || ""), dxyQuote.mid) ? (
            <p className="eds-type-caption text-[var(--eds-warning,#b45309)]">
              {integrityLabel(String(dxyQuote.status || ""), dxyQuote.mid)}
            </p>
          ) : null}
          <DxyNativeChart symbol="DXY" timeframe={dxyTf} height={chartH} liveQuote={dxyQuote} />
          <div className="mt-2 flex flex-wrap gap-2">
            <Button size="sm" className="ews-primary-cta" onClick={() => onCreateSignal("DXY")} data-testid="chart-signal-DXY">
              Создать сигнал
            </Button>
            <Link to="/workspace/crypto?view=analysis" data-testid="chart-analysis-DXY">
              <Button size="sm" className="ews-primary-cta">
                К анализу
              </Button>
            </Link>
            <Link to="/workspace/crypto?view=paper" data-testid="chart-paper-DXY">
              <Button size="sm" className="ews-primary-cta">
                Бумажная торговля
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}

function isOpenStatus(s: unknown) {
  return String(s || "").toUpperCase() === "OPEN";
}

export function PaperTradingPanel({
  account,
  orders,
  positions,
  onPlace,
  onClose,
  onCancel,
  onRefresh,
  message,
  quoteMid,
  placing = false,
  refreshing = false,
}: {
  account?: Record<string, unknown> | null;
  orders: Record<string, unknown>[];
  positions: Record<string, unknown>[];
  onPlace: (body: Record<string, unknown>) => void | Promise<void>;
  onClose: (positionId: string) => void;
  onCancel?: (orderId: string) => void;
  onRefresh: () => void | Promise<void>;
  message?: string | null;
  quoteMid?: number | null;
  placing?: boolean;
  refreshing?: boolean;
}) {
  const [side, setSide] = useState("BUY");
  const [orderType, setOrderType] = useState("MARKET");
  const [qty, setQty] = useState("1");
  const [entry, setEntry] = useState("");
  const [limit, setLimit] = useState("");
  const [sl, setSl] = useState("");
  const [tp, setTp] = useState("");
  const [instrument, setInstrument] = useState("EUR/USD");
  const [signalId, setSignalId] = useState("");
  const [analysisId, setAnalysisId] = useState("");
  const [agentId, setAgentId] = useState("");
  const [localPending, setLocalPending] = useState(false);
  const [localRefreshing, setLocalRefreshing] = useState(false);
  const busy = placing || localPending;
  const refreshBusy = refreshing || localRefreshing;

  const risk = useMemo(() => {
    const e = Number(entry) || Number(limit) || Number(quoteMid) || 0;
    const q = Number(qty) || 1;
    const bal = Number(account?.balance ?? 100000) || 100000;
    let potLoss: number | null = null;
    let potProfit: number | null = null;
    let riskPct: number | null = null;
    if (sl && e) {
      potLoss = Math.abs(e - Number(sl)) * q;
      riskPct = bal > 0 ? Math.round((10000 * potLoss) / bal) / 100 : null;
    }
    if (tp && e) potProfit = Math.abs(Number(tp) - e) * q;
    return { potLoss, potProfit, riskPct, entry: e };
  }, [entry, limit, quoteMid, qty, sl, tp, account]);

  return (
    <div className="space-y-3" data-testid="paper-trading">
      <p className="eds-type-caption text-[var(--eds-text-muted)]">
        Бумажная торговля (симуляция). Реальные сделки не исполняются. Котировка только с бэкенда.
      </p>

      <Card title="Демо-счёт">
        <div className="grid gap-2 sm:grid-cols-3 eds-type-small" data-testid="paper-account">
          <span>Баланс: {String(account?.balance ?? 100000)} USD</span>
          <span>Equity: {String(account?.equity ?? 100000)}</span>
          <span>Open P&amp;L: {String(account?.open_pnl ?? 0)}</span>
          <span>Realized P&amp;L: {String(account?.realized_pnl ?? 0)}</span>
          <span>Открытых позиций: {String(account?.open_positions ?? 0)}</span>
          <span>Win rate: {String(account?.win_rate ?? 0)}%</span>
          <span>Сделок: {String(account?.trades_count ?? 0)}</span>
        </div>
      </Card>

      <Card title="Новая бумажная сделка">
        <div className="grid gap-2 sm:grid-cols-2 eds-type-small">
          <label>
            Инструмент
            <select className="mt-1 w-full rounded border px-2 py-1" value={instrument} onChange={(e) => setInstrument(e.target.value)}>
              <option>EUR/USD</option>
              <option>DXY</option>
            </select>
          </label>
          <label>
            Сторона
            <select className="mt-1 w-full rounded border px-2 py-1" value={side} onChange={(e) => setSide(e.target.value)}>
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
            </select>
          </label>
          <label>
            Тип ордера
            <select className="mt-1 w-full rounded border px-2 py-1" value={orderType} onChange={(e) => setOrderType(e.target.value)}>
              <option value="MARKET">MARKET</option>
              <option value="LIMIT">LIMIT</option>
            </select>
          </label>
          <label>
            Размер позиции
            <Input className="mt-1" value={qty} onChange={(e) => setQty(e.target.value)} />
          </label>
          <label>
            Цена входа
            <Input
              className="mt-1"
              value={entry}
              onChange={(e) => setEntry(e.target.value)}
              placeholder={quoteMid != null ? String(quoteMid) : "из котировки"}
            />
          </label>
          {orderType === "LIMIT" ? (
            <label>
              Лимит-цена
              <Input className="mt-1" value={limit} onChange={(e) => setLimit(e.target.value)} />
            </label>
          ) : null}
          <label>
            Stop Loss
            <Input className="mt-1" value={sl} onChange={(e) => setSl(e.target.value)} />
          </label>
          <label>
            Take Profit
            <Input className="mt-1" value={tp} onChange={(e) => setTp(e.target.value)} />
          </label>
          <label>
            Risk %
            <Input className="mt-1" value={risk.riskPct != null ? String(risk.riskPct) : "—"} readOnly />
          </label>
          <label>
            Potential loss
            <Input className="mt-1" value={risk.potLoss != null ? String(risk.potLoss) : "—"} readOnly />
          </label>
          <label>
            Potential profit
            <Input className="mt-1" value={risk.potProfit != null ? String(risk.potProfit) : "—"} readOnly />
          </label>
          <label>
            Risk/Reward
            <Input
              className="mt-1"
              value={
                risk.potLoss && risk.potLoss > 0 && risk.potProfit != null
                  ? String(Math.round((risk.potProfit / risk.potLoss) * 1000) / 1000)
                  : "—"
              }
              readOnly
              data-testid="paper-rr"
            />
          </label>
          <label>
            Связь с сигналом (опционально)
            <Input
              className="mt-1"
              value={signalId}
              onChange={(e) => setSignalId(e.target.value)}
              placeholder="signal_id"
              data-testid="paper-link-signal"
            />
          </label>
          <label>
            Связь с анализом (опционально)
            <Input
              className="mt-1"
              value={analysisId}
              onChange={(e) => setAnalysisId(e.target.value)}
              placeholder="analysis_run_id"
              data-testid="paper-link-analysis"
            />
          </label>
          <label>
            Связь с агентом (опционально)
            <Input
              className="mt-1"
              value={agentId}
              onChange={(e) => setAgentId(e.target.value)}
              placeholder="agent_result_id"
              data-testid="paper-link-agent"
            />
          </label>
        </div>
        {message ? (
          <p
            className={`mt-2 eds-type-small ${message.toLowerCase().includes("ошиб") || message.includes("Не удалось") || message.includes("должен") ? "text-[var(--eds-danger,#b91c1c)]" : "text-[var(--eds-success,#15803d)]"}`}
            data-testid="paper-form-message"
            role="status"
          >
            {message}
          </p>
        ) : null}
        <div className="mt-2 flex flex-wrap gap-2">
          <Button
            size="sm"
            className="ews-primary-cta"
            disabled={busy}
            data-testid="paper-open-btn"
            onClick={() => {
              if (busy) return;
              setLocalPending(true);
              const idem =
                typeof crypto !== "undefined" && "randomUUID" in crypto
                  ? crypto.randomUUID()
                  : `idem_${Date.now()}_${Math.random().toString(16).slice(2)}`;
              void Promise.resolve(
                onPlace({
                  action: "place",
                  instrument,
                  side,
                  order_type: orderType,
                  quantity: Number(qty) || 1,
                  position_size: Number(qty) || 1,
                  entry_price: entry ? Number(entry) : undefined,
                  limit_price: limit ? Number(limit) : undefined,
                  stop_loss: sl ? Number(sl) : undefined,
                  take_profit: tp ? Number(tp) : undefined,
                  signal_id: signalId || undefined,
                  analysis_run_id: analysisId || undefined,
                  agent_result_id: agentId || undefined,
                  idempotency_key: idem,
                }),
              ).finally(() => setLocalPending(false));
            }}
          >
            {busy ? "Открываем…" : "Открыть бумажную сделку"}
          </Button>
          <Button
            size="sm"
            variant="secondary"
            disabled={refreshBusy}
            data-testid="paper-refresh-btn"
            onClick={() => {
              if (refreshBusy) return;
              setLocalRefreshing(true);
              void Promise.resolve(onRefresh()).finally(() => setLocalRefreshing(false));
            }}
          >
            {refreshBusy ? "Обновляем…" : "Обновить"}
          </Button>
        </div>
      </Card>

      <Card title="Открытые позиции">
        {positions.filter((p) => isOpenStatus(p.status)).length === 0 ? (
          <p className="eds-type-small text-[var(--eds-text-muted)]">Нет данных</p>
        ) : (
          positions
            .filter((p) => isOpenStatus(p.status))
            .map((p) => (
              <div key={String(p.position_id)} className="mb-2 border-b border-[var(--eds-border)] pb-2 eds-type-small">
                <p>
                  {String(p.instrument)} · {String(p.side)} · вход {String(p.entry_price)} · тек. {String(p.current_price ?? "—")}
                </p>
                <p>
                  Unrealized: {String(p.unrealized_pnl ?? "—")} · SL {String(p.stop_loss ?? "—")} · TP {String(p.take_profit ?? "—")}
                </p>
                <div className="mt-1 flex flex-wrap gap-2">
                  <Button size="sm" data-testid={`paper-close-${p.position_id}`} onClick={() => onClose(String(p.position_id))}>
                    Закрыть
                  </Button>
                  {p.signal_id ? (
                    <Link className="underline" to={`/workspace/crypto?view=signals&signal_id=${p.signal_id}`}>
                      Сигнал
                    </Link>
                  ) : null}
                  {p.analysis_run_id ? (
                    <Link className="underline" to={`/workspace/crypto?view=intel_history&run_id=${p.analysis_run_id}`}>
                      Анализ
                    </Link>
                  ) : null}
                </div>
              </div>
            ))
        )}
      </Card>

      <Card title="Ордера">
        {orders.length === 0 ? (
          <p className="eds-type-small text-[var(--eds-text-muted)]">Нет данных</p>
        ) : (
          orders.slice(0, 15).map((o) => (
            <div key={String(o.order_id)} className="mb-1 flex flex-wrap items-center gap-2 eds-type-small">
              <span>
                {String(o.created_at || "")} · {String(o.instrument)} · {String(o.order_type)} · {String(o.status)}
                {o.message_ru ? ` · ${String(o.message_ru)}` : ""}
              </span>
              {["PENDING", "DRAFT", "pending"].includes(String(o.status)) && onCancel ? (
                <Button size="sm" variant="secondary" onClick={() => onCancel(String(o.order_id))}>
                  Отменить
                </Button>
              ) : null}
            </div>
          ))
        )}
      </Card>
    </div>
  );
}

export function JournalPanel({ items }: { items: Record<string, unknown>[] }) {
  const [dateF, setDateF] = useState("");
  const [instF, setInstF] = useState("");
  const [resultF, setResultF] = useState("");
  const [agentF, setAgentF] = useState("");
  const [signalF, setSignalF] = useState("");
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null);

  const filtered = items.filter((j) => {
    if (dateF && !String(j.date || j.created_at || "").startsWith(dateF)) return false;
    if (instF && String(j.instrument || "") !== instF) return false;
    if (resultF && String(j.result || "") !== resultF) return false;
    if (agentF && !String(j.agent_result_id || "").includes(agentF)) return false;
    if (signalF && !String(j.signal_id || "").includes(signalF)) return false;
    return true;
  });

  if (!items.length) {
    return (
      <p className="eds-type-small text-[var(--eds-text-muted)]" data-testid="journal-empty">
        Бумажных сделок пока нет.
      </p>
    );
  }

  return (
    <div className="space-y-2" data-testid="trade-journal">
      <p className="eds-type-caption text-[var(--eds-text-muted)]">
        Журнал для оценки качества агентов. Обучение моделей не выполняется.
      </p>
      <div className="grid gap-2 sm:grid-cols-5 eds-type-small" data-testid="journal-filters">
        <Input placeholder="Дата" value={dateF} onChange={(e) => setDateF(e.target.value)} />
        <select className="rounded border px-2 py-1" value={instF} onChange={(e) => setInstF(e.target.value)}>
          <option value="">Инструмент</option>
          <option>EUR/USD</option>
          <option>DXY</option>
        </select>
        <select className="rounded border px-2 py-1" value={resultF} onChange={(e) => setResultF(e.target.value)}>
          <option value="">Результат</option>
          <option value="win">win</option>
          <option value="loss">loss</option>
          <option value="flat">flat</option>
        </select>
        <Input placeholder="Агент" value={agentF} onChange={(e) => setAgentF(e.target.value)} />
        <Input placeholder="Сигнал" value={signalF} onChange={(e) => setSignalF(e.target.value)} />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full eds-type-small" data-testid="journal-table">
          <thead>
            <tr className="text-left text-[var(--eds-text-muted)]">
              <th>Дата</th>
              <th>Инструмент</th>
              <th>BUY/SELL</th>
              <th>Вход</th>
              <th>Выход</th>
              <th>SL</th>
              <th>TP</th>
              <th>PnL</th>
              <th>Результат</th>
              <th>Источник</th>
              <th>Анализ</th>
              <th>Агент</th>
              <th>Длительность</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((j) => (
              <tr
                key={String(j.journal_id)}
                className="cursor-pointer border-t border-[var(--eds-border)] hover:bg-[var(--eds-surface-2,#f8f8f8)]"
                onClick={() => setSelected(j)}
              >
                <td>{String(j.date || String(j.created_at || "").slice(0, 10) || "—")}</td>
                <td>{String(j.instrument || "—")}</td>
                <td>{String(j.side || "—")}</td>
                <td>{String(j.entry ?? "—")}</td>
                <td>{String(j.exit ?? "—")}</td>
                <td>{String(j.stop_loss ?? "—")}</td>
                <td>{String(j.take_profit ?? "—")}</td>
                <td>{String(j.pnl ?? "—")}</td>
                <td>{String(j.result ?? "—")}</td>
                <td>{String(j.source || "paper")}</td>
                <td>{String(j.analysis_run_id || "—").slice(0, 10)}</td>
                <td>{String(j.agent_result_id || "—").slice(0, 10)}</td>
                <td>{j.duration_sec != null ? `${j.duration_sec} с` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {selected ? (
        <Card title="Детали сделки" data-testid="journal-detail">
          <div className="grid gap-1 eds-type-small">
            <p>Почему открыта сделка: {String(selected.why_opened || selected.notes || "—")}</p>
            <p>Какой сигнал: {String(selected.signal_id || "—")}</p>
            <p>Какой анализ: {String(selected.analysis_run_id || "—")}</p>
            <p>Какие агенты участвовали: {String(selected.agent_result_id || "—")}</p>
            <p>
              Какая уверенность была:{" "}
              {String((selected.agent_consensus as { confidence?: unknown } | undefined)?.confidence ?? "—")}
            </p>
            <p>Результат: {String(selected.result || "—")} · PnL {String(selected.pnl ?? "—")}</p>
          </div>
          <div className="mt-2 flex flex-wrap gap-2 eds-type-small">
            {selected.signal_id ? (
              <Link className="underline" to={`/workspace/crypto?view=signals&signal_id=${selected.signal_id}`}>
                Сигнал
              </Link>
            ) : null}
            {selected.analysis_run_id ? (
              <Link className="underline" to={`/workspace/crypto?view=intel_history&run_id=${selected.analysis_run_id}`}>
                Анализ
              </Link>
            ) : null}
            <Link className="underline" to="/workspace/crypto?view=paper">
              Бумажная сделка
            </Link>
            <Link className="underline" to="/workspace/crypto?view=calendar">
              Календарь
            </Link>
            <Button size="sm" variant="secondary" onClick={() => setSelected(null)}>
              Закрыть
            </Button>
          </div>
        </Card>
      ) : null}
    </div>
  );
}

function playBeep() {
  try {
    const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Ctx) return;
    const ctx = new Ctx();
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.connect(g);
    g.connect(ctx.destination);
    o.frequency.value = 880;
    g.gain.value = 0.05;
    o.start();
    setTimeout(() => {
      o.stop();
      void ctx.close();
    }, 180);
  } catch {
    /* ignore */
  }
}

export function SignalNotificationsPanel({
  items,
  onAct,
}: {
  items: Record<string, unknown>[];
  onAct: (notificationId: string, action: string) => void;
}) {
  useEffect(() => {
    const triggered = items.filter((n) => String(n.status) === "TRIGGERED" && n.sound);
    if (triggered.length && typeof Notification !== "undefined" && Notification.permission === "granted") {
      playBeep();
    }
  }, [items]);

  const requestPerm = async () => {
    if (typeof Notification === "undefined") return;
    await Notification.requestPermission();
  };

  return (
    <div className="space-y-2" data-testid="signal-notifications">
      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant="secondary" onClick={() => void requestPerm()}>
          Разрешить звук браузера
        </Button>
        <Link className="eds-type-small underline" to="/workspace/crypto?view=signals">
          Центр сигналов
        </Link>
      </div>
      {items.length === 0 ? <p className="eds-type-small text-[var(--eds-text-muted)]">Нет уведомлений</p> : null}
      {items.map((n) => (
        <Card key={String(n.notification_id)} title={String(n.title || "Уведомление")}>
          <p className="eds-type-small">
            {String(n.status_ru || n.status)} · {String(n.instrument || "")} · {String(n.created_at || "")}
          </p>
          <p className="eds-type-caption">{String(n.body || "")}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <Button size="sm" onClick={() => onAct(String(n.notification_id), "ack")}>
              Подтвердить
            </Button>
            <Link
              className="eds-type-small underline"
              to={
                (n.links as { paper?: string } | undefined)?.paper
                  ? `/workspace/crypto${String((n.links as { paper?: string }).paper)}`
                  : n.kind === "paper_opened" || n.kind === "paper_closed" || String(n.title || "").includes("бумаж")
                    ? "/workspace/crypto?view=paper"
                    : `/workspace/crypto?view=signals&signal_id=${n.signal_id || ""}`
              }
            >
              Открыть
            </Link>
            {(n.links as { journal?: string } | undefined)?.journal ? (
              <Link className="eds-type-small underline" to={`/workspace/crypto${String((n.links as { journal?: string }).journal)}`}>
                Журнал
              </Link>
            ) : null}
            <Button size="sm" variant="secondary" onClick={() => onAct(String(n.notification_id), "disable")}>
              Отключить
            </Button>
          </div>
        </Card>
      ))}
    </div>
  );
}

export function CrossLinkBar({
  signalId,
  analysisId,
  calendarHint,
}: {
  signalId?: string;
  analysisId?: string;
  calendarHint?: string;
}) {
  return (
    <div className="flex flex-wrap gap-3 eds-type-small" data-testid="cross-links">
      <Link className="underline" to="/workspace/crypto?view=charts">
        Графики
      </Link>
      <Link className="underline" to="/workspace/crypto?view=analysis">
        Анализы
      </Link>
      <Link className="underline" to="/workspace/crypto?view=specialists">
        AI-специалисты
      </Link>
      <Link className="underline" to={signalId ? `/workspace/crypto?view=signals&signal_id=${signalId}` : "/workspace/crypto?view=signals"}>
        Сигналы
      </Link>
      <Link className="underline" to="/workspace/crypto?view=notifications">
        Уведомления
      </Link>
      <Link className="underline" to="/workspace/crypto?view=calendar">
        Календарь{calendarHint ? ` · ${calendarHint}` : ""}
      </Link>
      <Link className="underline" to="/workspace/crypto?view=paper">
        Бумажная торговля
      </Link>
      <Link className="underline" to="/workspace/crypto?view=journal">
        Журнал
      </Link>
      <Link className="underline" to={analysisId ? `/workspace/crypto?view=intel_history&run_id=${analysisId}` : "/workspace/crypto?view=intel_history"}>
        История
      </Link>
    </div>
  );
}
