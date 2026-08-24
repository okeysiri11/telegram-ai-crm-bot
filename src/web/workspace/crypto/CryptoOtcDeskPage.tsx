/**
 * Sprint 50.5 — Operator desk: notifications, calendar, paper demo, journal, cross-links.
 * OTC ops preserved. Paper = simulation only (no broker execution).
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Badge, Button, Card, Input } from "@/ui";
import {
  BusinessCabinetShell,
  type OpsNavItem,
  type OpsSection,
} from "../business-ops/BusinessCabinetShell";
import {
  asList,
  cryptoEnterpriseGet,
  cryptoFxIntelGet,
  cryptoFxIntelPost,
  cryptoTaPost,
  pick,
} from "../business-ops/opsApi";
import { resolveCabinetCaps } from "../business-ops/cabinetCapabilities";
import {
  CHART_TIMEFRAMES,
  CryptoTaChartProvider,
  getMarketChartProvider,
  NullChartProvider,
  setMarketChartProvider,
  type ChartSnapshot,
  type ChartTimeframe,
} from "./chartProvider";
import {
  loadAnalyses,
  loadSpecialists,
  loadWatchlist,
  loadAgentSettings,
  loadChartInstrumentPrefs,
  saveAgentSettings,
  saveAnalyses,
  saveChartInstrumentPrefs,
  saveSpecialists,
  saveWatchlist,
  type AnalysisConfig,
  type SpecialistPref,
} from "./otcPrefs";
import { useAuthStore } from "@/auth/authStore";
import { TradingViewEmbed } from "./TradingViewEmbed";
import {
  AnalysisResultPanel,
  NewsFeedPanel,
  TechnicalSummaryCards,
} from "./cryptoIntelPanels";
import {
  CrossLinkBar,
  DualChartsPanel,
  JournalPanel,
  PaperTradingPanel,
  SignalNotificationsPanel,
} from "./paperTradingPanels";
import { OperatorCalendarPanel } from "./operatorCalendar";
import {
  SignalCreateForm,
  SpecialistSettingsPanel,
  defaultSpecialistSettings,
  type SpecialistSettings,
} from "./specialistAndSignalPanels";

const NAV_BASE: OpsNavItem[] = [
  { id: "home", label: "Главная" },
  { id: "markets", label: "Рынки" },
  { id: "quotes", label: "Котировки" },
  { id: "charts", label: "Графики" },
  { id: "pairs", label: "Мои инструменты" },
  { id: "analysis", label: "Анализы" },
  { id: "specialists", label: "AI-специалисты" },
  { id: "signals", label: "Сигналы" },
  { id: "news", label: "Новости" },
  { id: "calendar", label: "Календарь" },
  { id: "intel_history", label: "История анализов" },
  { id: "paper", label: "Бумажная торговля" },
  { id: "journal", label: "Журнал" },
  { id: "deals", label: "OTC-сделки" },
  { id: "orders", label: "Ордера" },
  { id: "wallets", label: "Кошельки" },
  { id: "transfers", label: "Переводы" },
  { id: "history", label: "История OTC" },
  { id: "notifications", label: "Уведомления" },
  { id: "settings", label: "Настройки" },
];

const SUGGESTED = ["EUR/USD", "DXY", "GBP/USD", "USD/UAH", "EUR/UAH", "BTC/USDT"];

type HealthMap = Record<string, { status?: string; label?: string; message?: string; last_update?: string }>;

function statusRu(s?: string) {
  if (s === "connected") return "Подключено";
  if (s === "error") return "Источник недоступен";
  if (s === "needs_config") return "Требуется настройка";
  if (s === "stale" || s === "cached") return "Данные устарели";
  if (s === "partial" || s === "insufficient_data") return "Частичные данные";
  if (s === "empty") return "Нет данных";
  return "Не подключено";
}

export function CryptoOtcDeskPage() {
  const caps = resolveCabinetCaps("crypto");
  const tenantId = (useAuthStore.getState().user as { tenantId?: string } | undefined)?.tenantId;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [watchlist, setWatchlist] = useState(() => loadWatchlist(tenantId));
  const [selected, setSelected] = useState(watchlist[0] || "EUR/USD");
  const [timeframe, setTimeframe] = useState<ChartTimeframe>("1h");
  const [chart, setChart] = useState<ChartSnapshot | null>(null);
  const [analyses, setAnalyses] = useState(() => loadAnalyses(tenantId));
  const [specialists, setSpecialists] = useState(() => loadSpecialists(tenantId));
  const [signals, setSignals] = useState<Record<string, unknown>[]>([]);
  const [eurusd, setEurusd] = useState<Record<string, unknown>>({});
  const [dxy, setDxy] = useState<Record<string, unknown>>({});
  const [health, setHealth] = useState<HealthMap>({});
  const [newPair, setNewPair] = useState("");
  const [runMsg, setRunMsg] = useState<string | null>(null);
  const [analysisDisplay, setAnalysisDisplay] = useState<Record<string, unknown> | null>(null);
  const [taEurusd, setTaEurusd] = useState<Record<string, unknown> | null>(null);
  const [taDxy, setTaDxy] = useState<Record<string, unknown> | null>(null);
  const [taTf, setTaTf] = useState("1H");
  const [newsItems, setNewsItems] = useState<Record<string, unknown>[]>([]);
  const [newsFilter, setNewsFilter] = useState("Все");
  const [newsLoading, setNewsLoading] = useState(false);
  const [macroEvents, setMacroEvents] = useState<Record<string, unknown>[]>([]);
  const [intelHistory, setIntelHistory] = useState<Record<string, unknown>[]>([]);
  const [historyDetail, setHistoryDetail] = useState<Record<string, unknown> | null>(null);
  const [paperOrders, setPaperOrders] = useState<Record<string, unknown>[]>([]);
  const [paperPositions, setPaperPositions] = useState<Record<string, unknown>[]>([]);
  const [journalItems, setJournalItems] = useState<Record<string, unknown>[]>([]);
  const [paperMsg, setPaperMsg] = useState<string | null>(null);
  const [paperAccount, setPaperAccount] = useState<Record<string, unknown> | null>(null);
  const [paperPlacing, setPaperPlacing] = useState(false);
  const [paperRefreshing, setPaperRefreshing] = useState(false);
  const [eurusdTf, setEurusdTf] = useState<ChartTimeframe>(() => (loadChartInstrumentPrefs(tenantId).eurusdTf as ChartTimeframe) || "1h");
  const [dxyTf, setDxyTf] = useState<ChartTimeframe>(() => (loadChartInstrumentPrefs(tenantId).dxyTf as ChartTimeframe) || "1h");
  const [calendarEvents, setCalendarEvents] = useState<Record<string, unknown>[]>([]);
  const [calFilters, setCalFilters] = useState<Record<string, boolean>>({
    macro: true,
    news: true,
    analysis: true,
    agent: true,
    signal: true,
    session: true,
    paper: true,
    manual: true,
  });
  const [notifItems, setNotifItems] = useState<Record<string, unknown>[]>([]);
  const [scheduleJobs, setScheduleJobs] = useState<Record<string, Record<string, unknown>>>({});
  const [settingsAgentId, setSettingsAgentId] = useState<string | null>(null);
  const [agentCfgMap, setAgentCfgMap] = useState<Record<string, SpecialistSettings>>({});
  const [signalFormOpen, setSignalFormOpen] = useState(false);
  const [signalFormDefaults, setSignalFormDefaults] = useState<Partial<Record<string, string | number | boolean>>>({});
  const [searchParams] = useSearchParams();
  const [bundle, setBundle] = useState<{
    markets: Record<string, unknown>[];
    portfolio: Record<string, unknown>;
  }>({ markets: [], portfolio: {} });

  useEffect(() => {
    setMarketChartProvider(new CryptoTaChartProvider(cryptoTaPost));
    return () => setMarketChartProvider(new NullChartProvider());
  }, []);

  const persistWatch = (next: string[]) => {
    setWatchlist(next);
    saveWatchlist(next, tenantId);
    if (!next.includes(selected) && next[0]) setSelected(next[0]);
  };

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [snap, m, p, sig] = await Promise.all([
        cryptoFxIntelGet("/snapshot"),
        cryptoEnterpriseGet("/markets"),
        cryptoEnterpriseGet("/portfolio"),
        cryptoFxIntelGet("/signals"),
      ]);
      if (snap.ok && snap.json && typeof snap.json === "object") {
        const j = snap.json as Record<string, unknown>;
        setEurusd((j.eurusd as Record<string, unknown>) || {});
        setDxy((j.dxy as Record<string, unknown>) || {});
        setHealth((j.health as HealthMap) || {});
      }
      setBundle({
        markets: asList(m.json, ["markets", "items", "data"]) as Record<string, unknown>[],
        portfolio: (p.json && typeof p.json === "object" ? p.json : {}) as Record<string, unknown>,
      });
      setSignals(asList(sig.json) as Record<string, unknown>[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  const loadChart = useCallback(async () => {
    const snap = await getMarketChartProvider().loadChart(selected, timeframe);
    // Overlay live FX quote when available (honest: only if connected)
    if (selected === "EUR/USD" && eurusd.mid) {
      setChart({
        ...snap,
        quote: {
          symbol: "EUR/USD",
          bid: String(eurusd.bid ?? eurusd.mid),
          ask: String(eurusd.ask ?? eurusd.mid),
          change: eurusd.change != null ? String(eurusd.change) : undefined,
          updatedAt: String(eurusd.fetched_at || ""),
          source: String(eurusd.source || "Источник котировок"),
        },
        status: eurusd.status === "connected" ? "connected" : snap.status,
        freshnessNote: String(eurusd.freshness || eurusd.message || snap.freshnessNote),
        message:
          eurusd.status === "connected"
            ? "Котировка EUR/USD от источника"
            : snap.message,
      });
      return;
    }
    if (selected === "DXY") {
      if (dxy.mid && dxy.status === "connected") {
        setChart({
          ...snap,
          quote: {
            symbol: "DXY",
            bid: String(dxy.bid ?? dxy.mid),
            ask: String(dxy.ask ?? dxy.mid),
            change: dxy.change != null ? String(dxy.change) : undefined,
            updatedAt: String(dxy.fetched_at || ""),
            source: String(dxy.source || "Источник DXY"),
          },
          status: "connected",
          freshnessNote: String(dxy.freshness || dxy.message || ""),
          message: "Котировка DXY от источника",
        });
        return;
      }
      setChart({
        ...snap,
        quote: null,
        status: (String(dxy.status || "needs_config") as ChartSnapshot["status"]),
        providerLabel: "Источник DXY",
        freshnessNote: String(dxy.message || "Требуется настройка"),
        message: String(dxy.message || "DXY: источник не подключён"),
      });
      return;
    }
    setChart(snap);
  }, [selected, timeframe, eurusd, dxy]);

  useEffect(() => {
    void load();
    void loadNews("Все");
    void loadMacro();
    void loadIntelHistory();
    void loadTechnical("1H");
    void loadPaper();
    void loadJournal();
    void loadNotifications();
    void loadCalendarBundle();
    void loadSchedule();
  }, [load]);

  useEffect(() => {
    void loadChart();
  }, [loadChart]);

  async function runSpecialist(id: string) {
    setRunMsg(null);
    const res = await cryptoFxIntelPost("/run", { specialist_id: id, tenant_id: tenantId || "default" });
    const json = (res.json || {}) as Record<string, unknown>;
    if (!res.ok || !json.ok) {
      setRunMsg(String(json.error || "Не удалось запустить анализ"));
      return;
    }
    const analysis = json.analysis as Record<string, unknown> | undefined;
    const signal = json.signal as Record<string, unknown> | undefined;
    const gaps = (json.dependency_gaps as string[]) || (json.missing_sources as string[]) || [];
    if (json.display && typeof json.display === "object") {
      setAnalysisDisplay(json.display as Record<string, unknown>);
    }
    if (signal) {
      setSignals((prev) => [signal, ...prev].slice(0, 50));
    }
    const next = specialists.map((s) =>
      s.id === id
        ? {
            ...s,
            lastReport: String(analysis?.created_at || new Date().toLocaleString("ru-RU")),
            lastResult: String(analysis?.direction || "—"),
            confidence: analysis?.confidence != null ? String(analysis.confidence) : "—",
            notes: gaps.length ? gaps.join("; ") : s.notes,
            status: gaps.length && id === "dxy" ? ("needs_config" as const) : ("configured" as const),
          }
        : s,
    );
    setSpecialists(next);
    saveSpecialists(next, tenantId);
    if (signal) setSignals((prev) => [signal, ...prev].slice(0, 50));
    setRunMsg("Анализ сохранён. " + (gaps.length ? `Ограничения: ${gaps.join("; ")}` : ""));
    await load();
  }

  const quoteRows = useMemo(() => {
    const rows = watchlist.map((pair) => {
      if (pair === "EUR/USD") {
        return {
          id: pair,
          pair,
          bid: eurusd.bid != null ? String(eurusd.bid) : "—",
          ask: eurusd.ask != null ? String(eurusd.ask) : "—",
          change: eurusd.change != null ? String(eurusd.change) : "—",
          updated: String(eurusd.fetched_at || "нет данных"),
          source: String(eurusd.source || statusRu(String(eurusd.status))),
        };
      }
      if (pair === "DXY") {
        return {
          id: pair,
          pair,
          bid: "—",
          ask: "—",
          change: "—",
          updated: "нет данных",
          source: statusRu(String(dxy.status || "needs_config")),
        };
      }
      const hit = bundle.markets.find((m) => {
        const sym = pick(m, "symbol", "pair", "name");
        return sym === pair || sym.includes(pair.split("/")[0] || "");
      });
      return {
        id: pair,
        pair,
        bid: hit ? pick(hit, "bid", "buy") : "—",
        ask: hit ? pick(hit, "ask", "sell") : "—",
        change: hit ? pick(hit, "change", "change_24h") : "—",
        updated: hit ? pick(hit, "updated_at", "ts") : "нет данных",
        source: hit ? pick(hit, "source") || "Источник котировок" : "Не подключено",
      };
    });
    return rows;
  }, [watchlist, eurusd, dxy, bundle.markets]);



  async function loadPaper() {
    const res = await cryptoFxIntelGet("/paper");
    const j = (res.json || {}) as Record<string, unknown>;
    setPaperOrders(Array.isArray(j.orders) ? (j.orders as Record<string, unknown>[]) : []);
    setPaperPositions(Array.isArray(j.positions) ? (j.positions as Record<string, unknown>[]) : []);
    setPaperAccount((j.account as Record<string, unknown>) || null);
    if (Array.isArray(j.journal)) {
      setJournalItems(j.journal as Record<string, unknown>[]);
    }
  }

  async function refreshPaperDesk() {
    setPaperRefreshing(true);
    try {
      const res = await cryptoFxIntelPost("/paper", { action: "refresh", tenant_id: tenantId || "default" });
      const j = (res.json || {}) as Record<string, unknown>;
      if (res.ok) {
        if (j.account) setPaperAccount(j.account as Record<string, unknown>);
        if (Array.isArray(j.orders)) setPaperOrders(j.orders as Record<string, unknown>[]);
        if (Array.isArray(j.positions)) setPaperPositions(j.positions as Record<string, unknown>[]);
        if (Array.isArray(j.journal)) setJournalItems(j.journal as Record<string, unknown>[]);
      }
      // Always refetch via GET for durable hydrate path (not stale React-only rerender)
      await loadPaper();
      await loadJournal();
      await loadNotifications();
    } finally {
      setPaperRefreshing(false);
    }
  }

  async function loadNotifications() {
    const res = await cryptoFxIntelGet("/notifications");
    const j = (res.json || {}) as Record<string, unknown>;
    setNotifItems(Array.isArray(j.items) ? (j.items as Record<string, unknown>[]) : []);
  }

  async function loadCalendarBundle(filters?: Record<string, boolean>) {
    const f = filters || calFilters;
    const res = await cryptoFxIntelPost("/calendar", { filters: f, tenant_id: tenantId || "default" });
    const j = (res.json || {}) as Record<string, unknown>;
    setCalendarEvents(Array.isArray(j.events) ? (j.events as Record<string, unknown>[]) : []);
  }

  async function cancelPaper(orderId: string) {
    const res = await cryptoFxIntelPost("/paper", {
      action: "cancel",
      order_id: orderId,
      tenant_id: tenantId || "default",
    });
    const j = (res.json || {}) as Record<string, unknown>;
    if (!res.ok || !j.ok) {
      setPaperMsg(String(j.error || "Не удалось отменить"));
      return;
    }
    setPaperMsg("Ордер отменён");
    await loadPaper();
  }

  async function actNotification(notificationId: string, action: string) {
    await cryptoFxIntelPost("/notifications", {
      notification_id: notificationId,
      action,
      tenant_id: tenantId || "default",
    });
    await loadNotifications();
    await load();
  }

  async function loadJournal() {
    const res = await cryptoFxIntelGet("/journal");
    const j = (res.json || {}) as Record<string, unknown>;
    setJournalItems(Array.isArray(j.items) ? (j.items as Record<string, unknown>[]) : []);
  }

  async function placePaper(body: Record<string, unknown>) {
    if (paperPlacing) return;
    setPaperPlacing(true);
    setPaperMsg(null);
    try {
      const res = await cryptoFxIntelPost("/paper", body);
      const j = (res.json || {}) as Record<string, unknown>;
      if (!res.ok || j.ok === false) {
        setPaperMsg(String(j.message_ru || j.error || "Ошибка открытия сделки"));
        return;
      }
      const warns = Array.isArray(j.risk_warnings) ? (j.risk_warnings as string[]) : [];
      setPaperMsg(
        String(j.message_ru || (warns.length ? `Ордер принят. ${warns.join(" ")}` : "Бумажная сделка открыта")),
      );
      await loadPaper();
      await loadJournal();
      await loadNotifications();
    } finally {
      setPaperPlacing(false);
    }
  }

  async function closePaper(positionId: string) {
    const res = await cryptoFxIntelPost("/paper", { action: "close", position_id: positionId, tenant_id: tenantId || "default" });
    const j = (res.json || {}) as Record<string, unknown>;
    if (!res.ok || !j.ok) {
      setPaperMsg(String(j.message_ru || j.error || "Не удалось закрыть"));
      return;
    }
    setPaperMsg("Позиция закрыта · запись в журнале");
    await loadPaper();
    await loadJournal();
  }

  async function createSignalFromChart(instrument: string) {
    const res = await cryptoFxIntelPost("/signals", {
      instrument,
      signal: "WAIT",
      timeframe,
      confidence: 0.4,
      source: "chart",
      tenant_id: tenantId || "default",
      reasons: ["Создан с графика"],
      price_trigger: eurusd.mid && instrument === "EUR/USD" ? { enabled: true, price: Number(eurusd.mid), direction: "cross" } : undefined,
    });
    const j = (res.json || {}) as Record<string, unknown>;
    if (res.ok && j.signal) {
      setSignals((prev) => [j.signal as Record<string, unknown>, ...prev].slice(0, 50));
      setRunMsg(`Сигнал создан: ${instrument}`);
      await loadNotifications();
      await loadCalendarBundle();
    } else {
      setRunMsg(String(j.error || "Не удалось создать сигнал"));
    }
  }

  async function runPreset(presetId: string) {
    setRunMsg(null);
    const res = await cryptoFxIntelPost("/run", {
      preset_id: presetId,
      tenant_id: tenantId || "default",
      timeframe: taTf,
    });
    const json = (res.json || {}) as Record<string, unknown>;
    if (!res.ok || !json.ok) {
      setRunMsg(String(json.error || "Не удалось запустить анализ"));
      return;
    }
    if (json.display && typeof json.display === "object") {
      setAnalysisDisplay(json.display as Record<string, unknown>);
    }
    if (json.signal && typeof json.signal === "object") {
      setSignals((prev) => [json.signal as Record<string, unknown>, ...prev].slice(0, 50));
    }
    const gaps = (json.missing_sources as string[]) || [];
    const nextAnalyses = analyses.map((a) =>
      a.id === presetId
        ? { ...a, lastRun: new Date().toLocaleString("ru-RU"), status: gaps.length ? "С ограничениями" : "Выполнен" }
        : a,
    );
    setAnalyses(nextAnalyses);
    saveAnalyses(nextAnalyses, tenantId);
    setRunMsg(gaps.length ? `Анализ сохранён. Ограничения: ${gaps.slice(0, 2).join("; ")}` : "Анализ выполнен и сохранён");
    void loadIntelHistory();
    void load();
  }

  async function loadTechnical(tf: string) {
    setTaTf(tf);
    const [e, d] = await Promise.all([
      cryptoFxIntelPost("/technical", { live: true, symbol: "EUR/USD", timeframe: tf }),
      cryptoFxIntelPost("/technical", { live: true, symbol: "DXY", timeframe: tf }),
    ]);
    setTaEurusd((e.json || null) as Record<string, unknown> | null);
    setTaDxy((d.json || null) as Record<string, unknown> | null);
  }

  async function loadNews(filter: string) {
    setNewsLoading(true);
    setNewsFilter(filter);
    try {
      const res = await cryptoFxIntelGet(`/news?filter=${encodeURIComponent(filter)}`);
      const items = Array.isArray((res.json as { items?: unknown })?.items)
        ? ((res.json as { items: Record<string, unknown>[] }).items)
        : [];
      setNewsItems(items);
    } finally {
      setNewsLoading(false);
    }
  }

  async function loadMacro() {
    const res = await cryptoFxIntelGet("/macro");
    const events = Array.isArray((res.json as { events?: unknown })?.events)
      ? ((res.json as { events: Record<string, unknown>[] }).events)
      : [];
    setMacroEvents(events);
  }

  async function loadIntelHistory() {
    const res = await cryptoFxIntelGet("/history");
    const items = Array.isArray((res.json as { items?: unknown })?.items)
      ? ((res.json as { items: Record<string, unknown>[] }).items)
      : [];
    setIntelHistory(items);
  }

  async function loadSchedule() {
    const res = await cryptoFxIntelGet("/schedule");
    const jobs = (res.json as { jobs?: Record<string, Record<string, unknown>> } | null)?.jobs;
    setScheduleJobs(jobs && typeof jobs === "object" ? jobs : {});
  }

  function nextRunLabel(presetId: string, enabled: boolean): string {
    const job = scheduleJobs[presetId];
    if (job?.next_run_ru) return String(job.next_run_ru);
    if (!enabled) return "Автозапуск не настроен";
    if (job?.next_run_at) return String(job.next_run_at);
    return "Автозапуск не настроен";
  }

  async function saveSchedule(presetId: string, patch: Record<string, unknown>) {
    const res = await cryptoFxIntelPost("/schedule", { preset_id: presetId, tenant_id: tenantId || "default", ...patch });
    if (!res.ok) {
      setRunMsg(String((res.json as { error?: string } | null)?.error || "Scheduler unavailable"));
      return;
    }
    const jobs = (res.json as { jobs?: Record<string, Record<string, unknown>> } | null)?.jobs;
    if (jobs) setScheduleJobs(jobs);
    else await loadSchedule();
  }

  async function submitSignalForm(body: Record<string, unknown>) {
    const res = await cryptoFxIntelPost("/signals", { ...body, tenant_id: tenantId || "default" });
    const j = (res.json || {}) as Record<string, unknown>;
    if (!res.ok || j.ok === false) {
      setRunMsg(String(j.error || "Signal creation failed"));
      return;
    }
    if (j.signal) setSignals((prev) => [j.signal as Record<string, unknown>, ...prev].slice(0, 50));
    setSignalFormOpen(false);
    setRunMsg("Сигнал сохранён");
    await load();
    await loadNotifications();
  }


  async function openHistory(runId: string) {
    const res = await cryptoFxIntelGet(`/history/${encodeURIComponent(runId)}`);
    if (res.ok && res.json && typeof res.json === "object") {
      setHistoryDetail(res.json as Record<string, unknown>);
      const run = (res.json as { run?: { payload?: Record<string, unknown> } }).run;
      if (run?.payload) setAnalysisDisplay(run.payload);
    }
  }

  function updateAnalysis(id: string, patch: Partial<AnalysisConfig>) {
    const next = analyses.map((a) => {
      if (a.id !== id) return a;
      const merged = { ...a, ...patch, updatedAt: new Date().toISOString() };
      const enabled = merged.enabled;
      merged.status = enabled ? "Активен" : "Выключен";
      return merged;
    });
    setAnalyses(next);
    saveAnalyses(next, tenantId);
  }

  const chartPanel = (
    <div className="space-y-3">
      <CrossLinkBar signalId={searchParams.get("signal_id") || undefined} analysisId={searchParams.get("run_id") || undefined} />
      <DualChartsPanel
        eurusdTf={eurusdTf}
        dxyTf={dxyTf}
        onEurusdTf={(tf) => {
          setEurusdTf(tf);
          setTimeframe(tf);
          saveChartInstrumentPrefs(
            { ...loadChartInstrumentPrefs(tenantId), primary: "EUR/USD", comparison: "DXY", eurusdTf: tf, dxyTf },
            tenantId,
          );
        }}
        onDxyTf={(tf) => {
          setDxyTf(tf);
          saveChartInstrumentPrefs(
            { ...loadChartInstrumentPrefs(tenantId), primary: "EUR/USD", comparison: "DXY", eurusdTf, dxyTf: tf },
            tenantId,
          );
        }}
        timeframes={CHART_TIMEFRAMES}
        eurusdQuote={eurusd}
        dxyQuote={dxy}
        onCreateSignal={(sym) => {
          setSignalFormDefaults({ instrument: sym, kind: "price_alert", source: "chart", title: `Сигнал ${sym}` });
          setSignalFormOpen(true);
        }}
        layout="vertical"
      />
      {signalFormOpen && searchParams.get("view") === "charts" ? (
        <SignalCreateForm defaults={signalFormDefaults} onSubmit={(b) => void submitSignalForm(b)} onCancel={() => setSignalFormOpen(false)} />
      ) : null}
      <p className="eds-type-caption text-[var(--eds-text-muted)]">AI-анализ, не является гарантией результата.</p>
    </div>
  );

  const pairsPanel = (
    <Card title="Управление парами">
      <div className="flex flex-wrap gap-2" data-testid="otc-watchlist-form">
        <Input
          placeholder="EUR/USD"
          value={newPair}
          onChange={(e) => setNewPair(e.target.value)}
          className="max-w-xs"
        />
        <Button
          size="sm"
          className="ews-primary-cta"
          onClick={() => {
            const p = newPair.trim().toUpperCase().replace("-", "/");
            if (!p) return;
            if (!watchlist.includes(p)) persistWatch([...watchlist, p]);
            setNewPair("");
          }}
        >
          Добавить пару
        </Button>
        {SUGGESTED.filter((p) => !watchlist.includes(p)).map((p) => (
          <Button key={p} size="sm" variant="secondary" onClick={() => persistWatch([...watchlist, p])}>
            + {p}
          </Button>
        ))}
      </div>
    </Card>
  );

  const analysisPanel = (
    <div className="space-y-3" data-testid="otc-analyses">
      <CrossLinkBar analysisId={String((analysisDisplay as { analysis_run_id?: string } | null)?.analysis_run_id || "")} />
      {runMsg ? <p className="eds-type-caption">{runMsg}</p> : null}
      {analyses.map((a) => (
        <Card key={a.id} title={a.name}>
          <div className="grid gap-2 sm:grid-cols-2 eds-type-small">
            <span>Инструменты: {a.instruments.join(", ")}</span>
            <span>Частота: {a.frequency}</span>
            <span data-testid={`analysis-active-${a.id}`}>Автозапуск: {a.enabled ? "Включён" : "Выключен"}</span>
            <span>
              Расписание:{" "}
              {String(scheduleJobs[a.id]?.schedule_ru || (a.enabled ? "—" : "Автозапуск не настроен"))}
            </span>
            <span>Последний запуск: {String(scheduleJobs[a.id]?.last_run_at || a.lastRun || "—")}</span>
            <span data-testid={`analysis-next-${a.id}`}>Следующий запуск: {nextRunLabel(a.id, a.enabled)}</span>
            <span>Результат: {String(scheduleJobs[a.id]?.last_result_ru || "—")}</span>
            <span>Timezone: {String(scheduleJobs[a.id]?.timezone || "Europe/Kyiv")}</span>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            <Button size="sm" className="ews-primary-cta" onClick={() => void runPreset(a.id).then(() => loadSchedule())}>
              Запустить сейчас
            </Button>
            <Button
              size="sm"
              variant="secondary"
              data-testid={`analysis-toggle-${a.id}`}
              onClick={() => {
                const next = !a.enabled;
                updateAnalysis(a.id, { enabled: next });
                void saveSchedule(a.id, { enabled: next });
              }}
            >
              {a.enabled ? "Выключить" : "Включить"}
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => {
                const hour = Number(scheduleJobs[a.id]?.hour ?? (a.id === "evening" ? 20 : a.id === "pre_us" ? 15 : a.id === "pre_europe" ? 7 : 7));
                const minute = Number(scheduleJobs[a.id]?.minute ?? (a.id === "pre_europe" ? 30 : 0));
                void saveSchedule(a.id, {
                  enabled: true,
                  hour,
                  minute,
                  timezone: String(scheduleJobs[a.id]?.timezone || "Europe/Kyiv"),
                });
                updateAnalysis(a.id, { enabled: true });
              }}
            >
              Настроить расписание
            </Button>
            <Link className="eds-type-small underline" to="/workspace/crypto?view=signals">
              Сигнал
            </Link>
            <Link className="eds-type-small underline" to="/workspace/crypto?view=paper">
              Бумажная торговля
            </Link>
            <Link className="eds-type-small underline" to="/workspace/crypto?view=intel_history">
              История
            </Link>
          </div>
        </Card>
      ))}
      <TechnicalSummaryCards eurusd={taEurusd} dxy={taDxy} timeframe={taTf} onTimeframe={(tf) => void loadTechnical(tf)} />
      <AnalysisResultPanel
        display={analysisDisplay}
        onCreateSignal={() => {
          setSignalFormDefaults({
            instrument: "EUR/USD",
            kind: "analysis_result",
            source: "analysis",
            title: `Анализ → ${String((analysisDisplay as { final_result?: string } | null)?.final_result || "WAIT")}`,
            analysis_run_id: String((analysisDisplay as { analysis_run_id?: string } | null)?.analysis_run_id || ""),
          });
          setSignalFormOpen(true);
        }}
      />
      {signalFormOpen ? (
        <SignalCreateForm defaults={signalFormDefaults} onSubmit={(b) => void submitSignalForm(b)} onCancel={() => setSignalFormOpen(false)} />
      ) : null}
    </div>
  );

  const specialistsPanel = (
    <div className="space-y-3" data-testid="otc-specialists">
      {runMsg ? <p className="eds-type-caption">{runMsg}</p> : null}
      <div className="grid gap-3 sm:grid-cols-2">
        {specialists.map((s: SpecialistPref) => (
          <Card key={s.id} title={s.name}>
            <p className="eds-type-small">Статус: {s.status === "configured" ? "Готов" : "Требуется настройка"}</p>
            <p className="eds-type-small">Инструменты: {s.instruments.join(", ")}</p>
            <p className="eds-type-small">Последний анализ: {s.lastReport}</p>
            <p className="eds-type-small">Результат: {s.lastResult || "—"}</p>
            <p className="eds-type-small">Уверенность: {s.confidence || "—"}</p>
            {s.notes ? <p className="eds-type-caption text-[var(--eds-text-muted)]">{s.notes}</p> : null}
            <p className="eds-type-caption text-[var(--eds-text-muted)]">
              {s.lastReport === "—" || !s.lastReport ? "Этот специалист ещё не запускался." : `История: ${s.lastReport}`}
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <Button size="sm" className="ews-primary-cta" onClick={() => void runSpecialist(s.id)}>
                Запустить
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => {
                  if (!agentCfgMap[s.id]) {
                    setAgentCfgMap((m) => ({ ...m, [s.id]: defaultSpecialistSettings(s.id) }));
                  }
                  setSettingsAgentId(s.id);
                }}
              >
                Настроить
              </Button>
              <Link className="eds-type-small underline" to="/workspace/crypto?view=analysis">
                Анализ
              </Link>
              <Link className="eds-type-small underline" to="/workspace/crypto?view=signals">
                Сигнал
              </Link>
              <Link className="eds-type-small underline" to="/workspace/crypto?view=intel_history">
                История
              </Link>
            </div>
          </Card>
        ))}
      </div>
      {settingsAgentId ? (
        <SpecialistSettingsPanel
          agentId={settingsAgentId}
          agentName={specialists.find((x) => x.id === settingsAgentId)?.name || settingsAgentId}
          value={agentCfgMap[settingsAgentId] || defaultSpecialistSettings(settingsAgentId)}
          onSave={(cfg) => {
            setAgentCfgMap((m) => ({ ...m, [settingsAgentId]: cfg }));
            const next = specialists.map((x) =>
              x.id === settingsAgentId
                ? {
                    ...x,
                    status: "configured" as const,
                    instruments: cfg.instruments,
                    enabled: cfg.enabled,
                    weight: cfg.weight,
                    notes: `weight=${cfg.weight}; min_conf=${cfg.minimum_confidence}`,
                  }
                : x,
            );
            setSpecialists(next);
            saveSpecialists(next, tenantId);
            const settings = loadAgentSettings(tenantId);
            settings[settingsAgentId] = {
              enabled: cfg.enabled,
              weight: cfg.weight,
              instruments: cfg.instruments,
            };
            saveAgentSettings(settings, tenantId);
            setRunMsg("Настройки специалиста сохранены");
          }}
          onClose={() => setSettingsAgentId(null)}
        />
      ) : null}
      <p className="eds-type-caption text-[var(--eds-text-muted)]">
        AI-анализ, не является гарантией результата.
      </p>
    </div>
  );

  const newsPanel = (
    <NewsFeedPanel items={newsItems} filter={newsFilter} onFilter={(f) => void loadNews(f)} loading={newsLoading} />
  );

  const calendarPanel = (
    <div className="space-y-3">
      <CrossLinkBar />
      <OperatorCalendarPanel
        events={calendarEvents.length ? calendarEvents : macroEvents}
        filters={calFilters}
        onFiltersChange={(next) => {
          setCalFilters(next);
          void loadCalendarBundle(next);
        }}
        onCreateManual={(body) => {
          void cryptoFxIntelPost("/calendar", { ...body, tenant_id: tenantId || "default" }).then(() =>
            loadCalendarBundle(),
          );
        }}
      />
    </div>
  );

  const notificationsPanel = (
    <div className="space-y-3">
      <CrossLinkBar />
      <SignalNotificationsPanel items={notifItems} onAct={(id, a) => void actNotification(id, a)} />
      <p className="eds-type-caption text-[var(--eds-text-muted)]">Telegram и email в этом спринте не требуются.</p>
    </div>
  );

  const intelHistoryPanel = (
    <div className="space-y-3" data-testid="intel-history">
      <Button size="sm" variant="secondary" onClick={() => void loadIntelHistory()}>
        Обновить
      </Button>
      {intelHistory.map((h) => (
        <Card key={String(h.analysis_run_id || h.analysis_id)} title={String(h.preset_id || h.agent || "Анализ")}>
          <p className="eds-type-small">
            {String(h.instrument || "EUR/USD")} · {String(h.direction || "—")} ·{" "}
            {h.confidence != null ? `${Math.round(Number(h.confidence) * 100)}%` : "—"}
          </p>
          <p className="eds-type-caption">{String(h.created_at || "—")}</p>
          <Button size="sm" className="mt-2 ews-primary-cta" onClick={() => void openHistory(String(h.analysis_run_id || h.analysis_id))}>
            Открыть результат
          </Button>
        </Card>
      ))}
      {historyDetail ? (
        <Card title="Снимок на момент анализа">
          <p className="eds-type-small">Цена: {String(((historyDetail as { run?: Record<string, unknown> }).run || {}).price_at_analysis || "—")}</p>
          <p className="eds-type-small">DXY: {String(((historyDetail as { run?: Record<string, unknown> }).run || {}).dxy_at_analysis || "—")}</p>
        </Card>
      ) : null}
      <AnalysisResultPanel display={analysisDisplay} />
    </div>
  );

  const paperPanel = (
    <div className="space-y-3">
      <CrossLinkBar />
      <PaperTradingPanel
        account={paperAccount}
        orders={paperOrders}
        positions={paperPositions}
        placing={paperPlacing}
        refreshing={paperRefreshing}
        onPlace={(body) =>
          placePaper({
            ...body,
            tenant_id: tenantId || "default",
            analysis_run_id: body.analysis_run_id || searchParams.get("run_id") || signalFormDefaults.analysis_run_id,
            signal_id: body.signal_id || searchParams.get("signal_id") || undefined,
            risk_settings: agentCfgMap.risk || defaultSpecialistSettings("risk"),
            idempotency_key:
              body.idempotency_key || `paper_${Date.now()}_${Math.random().toString(16).slice(2)}`,
          })
        }
        onClose={(id) => void closePaper(id)}
        onCancel={(id) => void cancelPaper(id)}
        onRefresh={() => refreshPaperDesk()}
        message={paperMsg}
        quoteMid={eurusd.mid != null ? Number(eurusd.mid) : null}
      />
    </div>
  );

  const journalPanel = (
    <div className="space-y-3">
      <CrossLinkBar />
      <JournalPanel items={journalItems} />
    </div>
  );

  const settingsPanel = (
    <div className="grid gap-3 sm:grid-cols-2" data-testid="otc-settings-health">
      {(
        [
          ["quotes", "Источники котировок"],
          ["tradingview", "TradingView"],
          ["news", "Новости"],
          ["macro_calendar", "Экономический календарь"],
          ["ai_analysis", "AI-анализ"],
          ["scheduler", "Расписание"],
          ["notifications", "Уведомления"],
        ] as const
      ).map(([key, label]) => {
        const h = health[key] || {};
        return (
          <Card key={key} title={label}>
            <p className="eds-type-small">{statusRu(h.status)}</p>
            <p className="eds-type-caption text-[var(--eds-text-muted)]">{h.message || "—"}</p>
            <p className="eds-type-caption">Последнее обновление: {h.last_update || "—"}</p>
          </Card>
        );
      })}
      <Card title="Инструменты">
        <p className="eds-type-small">По умолчанию: EUR/USD, DXY</p>
      </Card>
      <Card title="Часовой пояс">
        <p className="eds-type-small">{Intl.DateTimeFormat().resolvedOptions().timeZone}</p>
      </Card>
    </div>
  );

  const nav = useMemo(
    () =>
      NAV_BASE.map((n) => ({
        ...n,
        hidden: (n.id === "settings" && !caps.canConfigure) || (caps.isCustomer && !["home", "quotes", "charts"].includes(n.id)),
      })),
    [caps],
  );

  const sections: Record<string, OpsSection> = useMemo(() => {
    return {
      home: {
        id: "home",
        title: "Главная · EUR/USD и DXY",
        description: "Рыночная аналитика FX + операционный OTC-стол.",
        columns: [
          { key: "metric", label: "Показатель" },
          { key: "value", label: "Значение" },
        ],
        cards: [
          { label: "EUR/USD", value: eurusd.mid != null ? String(eurusd.mid) : "нет данных" },
          { label: "DXY", value: dxy.mid != null ? String(dxy.mid) : "нет данных" },
          { label: "Мои пары", value: String(watchlist.length) },
          { label: "Сигналы", value: String(signals.length) },
        ],
        rows: [
          { metric: "Источник котировок", value: statusRu(String(eurusd.status || health.quotes?.status)) },
          { metric: "Антифрод", value: "Активен" },
          { metric: "Графики", value: statusRu(chart?.status) },
        ],
        quickActions: [
          { label: "Графики", to: "/workspace/crypto?view=charts" },
          { label: "Анализы", to: "/workspace/crypto?view=analysis" },
          { label: "AI-специалисты", to: "/workspace/crypto?view=specialists" },
          { label: "Подтверждение выплаты", to: "/crypto-otc/payout/demo" },
        ],
        integrationNote: "AI-анализ, не является гарантией результата.",
      },
      markets: {
        id: "markets",
        title: "Рынки",
        description: "Фокус: EUR/USD и DXY.",
        columns: [
          { key: "symbol", label: "Инструмент" },
          { key: "mid", label: "Курс" },
          { key: "source", label: "Источник" },
          { key: "status", label: "Состояние" },
        ],
        rows: [
          {
            symbol: "EUR/USD",
            mid: eurusd.mid != null ? String(eurusd.mid) : "—",
            source: String(eurusd.source || "—"),
            status: statusRu(String(eurusd.status)),
          },
          {
            symbol: "DXY",
            mid: "—",
            source: "—",
            status: statusRu(String(dxy.status || "needs_config")),
          },
        ],
      },
      quotes: {
        id: "quotes",
        title: "Котировки",
        description: "Источник и свежесть без выдуманных цен.",
        columns: [
          { key: "pair", label: "Пара" },
          { key: "bid", label: "Bid" },
          { key: "ask", label: "Ask" },
          { key: "change", label: "Изменение" },
          { key: "updated", label: "Обновлено" },
          { key: "source", label: "Источник" },
        ],
        rows: quoteRows,
        emptyTitle: "Инструментов пока нет. Добавьте EUR/USD или DXY.",
        emptyDescription: "Список пар пуст — добавьте инструмент вручную.",
      },
      charts: {
        id: "charts",
        title: "Графики",
        description: "Таймфреймы и состояние источника.",
        columns: [
          { key: "pair", label: "Пара" },
          { key: "tf", label: "ТФ" },
          { key: "status", label: "Статус" },
        ],
        rows: [{ pair: selected, tf: timeframe, status: statusRu(chart?.status) }],
        panel: chartPanel,
      },
      pairs: {
        id: "pairs",
        title: "Мои пары",
        description: "Watchlist. По умолчанию EUR/USD и DXY.",
        columns: [
          { key: "pair", label: "Пара" },
          { key: "source", label: "Источник" },
          { key: "updated", label: "Обновлено" },
        ],
        rows: quoteRows,
        panel: pairsPanel,
        rowActions: (row) => (
          <Button
            size="sm"
            variant="secondary"
            onClick={() => persistWatch(watchlist.filter((p) => p !== String(row.pair)))}
          >
            Удалить
          </Button>
        ),
      },
      analysis: {
        id: "analysis",
        title: "Анализы",
        description: "Профили обзоров. Автодоставка не настроена.",
        columns: [
          { key: "name", label: "Название" },
          { key: "instruments", label: "Инструменты" },
          { key: "frequency", label: "Частота" },
          { key: "enabled", label: "Активен" },
          { key: "last", label: "Последний запуск" },
          { key: "next", label: "Следующий запуск" },
          { key: "status", label: "Статус" },
        ],
        rows: analyses.map((a) => ({
          id: a.id,
          name: a.name,
          instruments: a.instruments.join(", "),
          frequency: a.frequency,
          enabled: a.enabled ? "Да" : "Нет",
          last: a.lastRun || "—",
          next: "—",
          status: a.status || "Автодоставка не настроена",
        })),
        panel: analysisPanel,
      },
      specialists: {
        id: "specialists",
        title: "AI-специалисты",
        description: "Консенсус и запуски через общий сервис анализа.",
        columns: [
          { key: "name", label: "Специалист" },
          { key: "status", label: "Статус" },
          { key: "last", label: "Последний анализ" },
        ],
        rows: specialists.map((s) => ({
          id: s.id,
          name: s.name,
          status: s.status,
          last: s.lastReport,
        })),
        panel: specialistsPanel,
      },
      signals: {
        id: "signals",
        title: "Сигналы",
        description: "Только аналитика. Сделки не исполняются.",
        columns: [
          { key: "time", label: "Время" },
          { key: "instrument", label: "Инструмент" },
          { key: "signal", label: "Сигнал" },
          { key: "tf", label: "Таймфрейм" },
          { key: "zone", label: "Зона" },
          { key: "conf", label: "Уверенность" },
          { key: "reason", label: "Причина" },
          { key: "status", label: "Статус" },
        ],
        rows: signals.map((s, i) => ({
          id: pick(s, "signal_id") || String(i),
          time: pick(s, "timestamp"),
          instrument: pick(s, "instrument"),
          signal: pick(s, "signal"),
          tf: pick(s, "timeframe"),
          zone: pick(s, "entry_zone") || "—",
          conf: pick(s, "confidence"),
          reason: Array.isArray(s.reasons) ? (s.reasons as string[]).join("; ") : "—",
          status: pick(s, "status"),
        })),
        emptyTitle: "Сигналов пока нет. Создайте сигнал по EUR/USD или DXY.",
        emptyDescription: "Сигналов пока нет. Создайте сигнал по EUR/USD или DXY.",
        emptyCtaLabel: "Создать сигнал",
        emptyCtaOnClick: () => void createSignalFromChart("EUR/USD"),
        integrationNote: "AI-анализ, не является гарантией результата.",
        rowActions: (row) => (
          <div className="flex flex-wrap gap-2 eds-type-small">
            <button
              type="button"
              className="underline"
              onClick={() =>
                void cryptoFxIntelPost("/signals/lifecycle", {
                  signal_id: String(row.id),
                  enabled: false,
                  tenant_id: tenantId || "default",
                }).then(() => load())
              }
            >
              Отключить
            </button>
            <button
              type="button"
              className="underline"
              onClick={() =>
                void cryptoFxIntelPost("/signals/lifecycle", {
                  signal_id: String(row.id),
                  enabled: true,
                  tenant_id: tenantId || "default",
                }).then(() => load())
              }
            >
              Включить
            </button>
            <Link className="underline" to="/workspace/crypto?view=paper">
              Бумажная торговля
            </Link>
            <Link className="underline" to="/workspace/crypto?view=intel_history">
              История
            </Link>
          </div>
        ),
      },
      deals: {
        id: "deals",
        title: "OTC-сделки",
        description: "Операционные сделки. Антифрод активен.",
        columns: [
          { key: "id", label: "ID" },
          { key: "status", label: "Статус" },
        ],
        rows: [],
        emptyTitle: "OTC-сделок пока нет.",
        emptyDescription: "Операционных OTC-сделок пока нет.",
        quickActions: [{ label: "Подтверждение выплаты", to: "/crypto-otc/payout/demo" }],
      },
      orders: {
        id: "orders",
        title: "Ордера",
        description: "Журнал ордеров.",
        columns: [
          { key: "id", label: "ID" },
          { key: "status", label: "Статус" },
        ],
        rows: [],
        emptyTitle: "Ордеров пока нет.",
        emptyDescription: "Операционных ордеров пока нет.",
      },
      wallets: {
        id: "wallets",
        title: "Кошельки",
        description: "Без секретных ключей.",
        columns: [
          { key: "asset", label: "Актив" },
          { key: "balance", label: "Баланс" },
        ],
        rows: asList((bundle.portfolio as { wallets?: unknown }).wallets || []).map((r, i) => {
          const row = r as Record<string, unknown>;
          return {
            id: pick(row, "id", "asset") || String(i),
            asset: pick(row, "asset", "symbol"),
            balance: pick(row, "balance", "total"),
          };
        }),
        emptyTitle: "Кошельков пока нет.",
        emptyDescription: "Подключённых кошельков пока нет.",
      },
      transfers: {
        id: "transfers",
        title: "Переводы",
        description: "Операционный журнал.",
        columns: [
          { key: "id", label: "ID" },
          { key: "status", label: "Статус" },
        ],
        rows: [],
        emptyTitle: "Переводов пока нет.",
        emptyDescription: "Переводов пока нет.",
      },
      history: {
        id: "history",
        title: "История",
        description: "Журнал desk.",
        columns: [
          { key: "when", label: "Когда" },
          { key: "event", label: "Событие" },
        ],
        rows: [],
        emptyTitle: "Событий истории пока нет.",
        emptyDescription: "Событий истории пока нет.",
      },
      notifications: {
        id: "notifications",
        title: "Уведомления",
        description: "In-app: ACTIVE / TRIGGERED / ACKNOWLEDGED / EXPIRED / DISABLED. Звук при разрешении браузера.",
        columns: [
          { key: "title", label: "Событие" },
          { key: "status", label: "Статус" },
          { key: "instrument", label: "Инструмент" },
        ],
        rows: notifItems.map((n) => ({
          title: String(n.title || "—"),
          status: String(n.status_ru || n.status || "—"),
          instrument: String(n.instrument || "—"),
        })),
        panel: notificationsPanel,
      },
      news: {
        id: "news",
        title: "Новости",
        description: "Fed + ECB. Оценка влияния без торговых советов.",
        columns: [
          { key: "published_at", label: "Время" },
          { key: "source", label: "Источник" },
          { key: "title", label: "Заголовок" },
          { key: "ai_assessment", label: "AI-оценка" },
        ],
        rows: newsItems.map((n) => ({
          published_at: String(n.published_at || "—"),
          source: String(n.source || "—"),
          title: String(n.title || "—"),
          ai_assessment: String(n.ai_assessment || n.sentiment || "—"),
        })),
        panel: newsPanel,
      },
      calendar: {
        id: "calendar",
        title: "Календарь",
        description: "Месяц / неделя / день. Макро, новости, анализы, сигналы, сессии, paper, ручные.",
        columns: [
          { key: "scheduled_at", label: "Время" },
          { key: "title", label: "Событие" },
          { key: "category", label: "Категория" },
          { key: "importance", label: "Важность" },
        ],
        rows: (calendarEvents.length ? calendarEvents : macroEvents).slice(0, 40).map((e) => ({
          scheduled_at: String(e.scheduled_at || "—"),
          title: String(e.title || e.event || "—"),
          category: String(e.category || e.country || "—"),
          importance: String(e.importance || "—"),
        })),
        panel: calendarPanel,
      },
      intel_history: {
        id: "intel_history",
        title: "История анализов",
        description: "Сохранённые прогоны со снимком данных.",
        emptyTitle: "Анализы ещё не выполнялись.",
        emptyDescription: "Анализы ещё не выполнялись.",
        columns: [
          { key: "created_at", label: "Дата" },
          { key: "preset_id", label: "Тип" },
          { key: "instrument", label: "Инструмент" },
          { key: "direction", label: "Направление" },
        ],
        rows: intelHistory.map((h) => ({
          created_at: String(h.created_at || "—"),
          preset_id: String(h.preset_id || "—"),
          instrument: String(h.instrument || "—"),
          direction: String(h.direction || "—"),
        })),
        panel: intelHistoryPanel,
      },
      paper: {
        id: "paper",
        title: "Бумажная торговля",
        description: "Симуляция market/limit + SL/TP. Без реального исполнения.",
        emptyTitle: "Бумажных сделок пока нет.",
        emptyDescription: "Бумажных сделок пока нет.",
        columns: [
          { key: "instrument", label: "Инструмент" },
          { key: "side", label: "Сторона" },
          { key: "status", label: "Статус" },
          { key: "pnl", label: "PnL" },
        ],
        rows: paperPositions.map((p) => ({
          instrument: String(p.instrument || "—"),
          side: String(p.side || "—"),
          status: String(p.status || "—"),
          pnl: p.pnl != null ? String(p.pnl) : "—",
        })),
        panel: paperPanel,
      },
      journal: {
        id: "journal",
        title: "Журнал",
        description: "Вход, выход, PnL, связь с сигналом и анализом.",
        emptyTitle: "Закрытых бумажных сделок пока нет.",
        emptyDescription: "Закрытых бумажных сделок пока нет.",
        columns: [
          { key: "instrument", label: "Инструмент" },
          { key: "pnl", label: "PnL" },
          { key: "signal_id", label: "Сигнал" },
          { key: "analysis_run_id", label: "Анализ" },
        ],
        rows: journalItems.map((j) => ({
          instrument: String(j.instrument || "—"),
          pnl: j.pnl != null ? String(j.pnl) : "—",
          signal_id: String(j.signal_id || "—"),
          analysis_run_id: String(j.analysis_run_id || "—"),
        })),
        panel: journalPanel,
      },
      settings: {
        id: "settings",
        title: "Настройки",
        description: "Состояние подключений.",
        columns: [
          { key: "item", label: "Раздел" },
          { key: "value", label: "Состояние" },
        ],
        rows: [
          { item: "Источник котировок", value: statusRu(health.quotes?.status) },
          { item: "TradingView", value: statusRu(health.tradingview?.status) },
          { item: "Новости", value: statusRu(health.news?.status) },
          { item: "Календарь", value: statusRu(health.macro_calendar?.status) },
        ],
        panel: settingsPanel,
      },
    };
  }, [
    eurusd,
    dxy,
    watchlist,
    signals,
    health,
    chart,
    quoteRows,
    selected,
    timeframe,
    analyses,
    specialists,
    bundle,
    chartPanel,
    pairsPanel,
    analysisPanel,
    specialistsPanel,
    newsPanel,
    calendarPanel,
    intelHistoryPanel,
    newsItems,
    macroEvents,
    intelHistory,
    analysisDisplay,
    taEurusd,
    taDxy,
    taTf,
    runMsg,
    paperPanel,
    journalPanel,
    paperOrders,
    paperPositions,
    journalItems,
    paperMsg,
    paperAccount,
    eurusdTf,
    dxyTf,
    calendarEvents,
    calFilters,
    notifItems,
    notificationsPanel,
    scheduleJobs,
    settingsAgentId,
    settingsPanel,
  ]);

  return (
    <>
      <BusinessCabinetShell
        verticalId="crypto"
        title="Crypto OTC"
        subtitle="EUR/USD · DXY · анализы · OTC"
        nav={nav}
        sections={sections}
        loading={loading}
        error={error}
        roleHint={caps.roleLabel}
        onRefresh={() => void load()}
        testId="crypto-otc-desk"
      />
      <p className="px-4 pb-4 eds-type-caption text-[var(--eds-text-muted)]">
        Антифрод выплат:{" "}
        <Link className="text-[var(--eds-primary)]" to="/crypto-otc/payout/demo">
          подтверждение
        </Link>
        .
      </p>
    </>
  );
}
