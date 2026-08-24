/**
 * Sprint 49.1 — chart provider boundary for OTC desk.
 * TradingView (or another provider) plugs in without rewriting Crypto workspace.
 */

export type ChartTimeframe = "1m" | "5m" | "15m" | "1h" | "4h" | "1D" | "1W";

export type ChartProviderStatus = "connected" | "not_connected" | "needs_config" | "error";

export type ChartQuote = {
  symbol: string;
  bid?: string;
  ask?: string;
  change?: string;
  updatedAt?: string;
  source: string;
};

export type ChartSnapshot = {
  symbol: string;
  timeframe: ChartTimeframe;
  status: ChartProviderStatus;
  providerId: string;
  providerLabel: string;
  quote: ChartQuote | null;
  freshnessNote: string;
  bars: Array<{ t: string; c: number }>;
  message: string;
};

export interface MarketChartProvider {
  id: string;
  label: string;
  asyncStatus(): Promise<ChartProviderStatus>;
  loadChart(symbol: string, timeframe: ChartTimeframe): Promise<ChartSnapshot>;
}

/** Default: no live feed — honest empty chart shell. */
export class NullChartProvider implements MarketChartProvider {
  id = "null";
  label = "Не подключено";

  async asyncStatus(): Promise<ChartProviderStatus> {
    return "not_connected";
  }

  async loadChart(symbol: string, timeframe: ChartTimeframe): Promise<ChartSnapshot> {
    return {
      symbol,
      timeframe,
      status: "not_connected",
      providerId: this.id,
      providerLabel: this.label,
      quote: null,
      freshnessNote: "Нет источника котировок",
      bars: [],
      message: "График недоступен: провайдер рынка не настроен. Подключите TradingView или market-data.",
    };
  }
}

/**
 * Optional TradingView / crypto-ta bridge.
 * Does not invent live prices; reports API response or needs_config.
 */
export class CryptoTaChartProvider implements MarketChartProvider {
  id = "crypto-ta";
  label = "Crypto TA / TradingView bridge";

  constructor(private post: (path: string, body: Record<string, unknown>) => Promise<{ ok: boolean; status: number; json: unknown }>) {}

  async asyncStatus(): Promise<ChartProviderStatus> {
    const res = await this.post("/tradingview", { action: "status" });
    if (!res.ok) return res.status === 0 ? "not_connected" : "needs_config";
    const j = res.json as Record<string, unknown>;
    if (j?.status === "connected") return "connected";
    return "needs_config";
  }

  async loadChart(symbol: string, timeframe: ChartTimeframe): Promise<ChartSnapshot> {
    const status = await this.asyncStatus();
    if (status !== "connected") {
      return {
        symbol,
        timeframe,
        status,
        providerId: this.id,
        providerLabel: this.label,
        quote: null,
        freshnessNote: "Провайдер не готов",
        bars: [],
        message:
          status === "needs_config"
            ? "Требуется настройка TradingView / crypto-ta."
            : "Провайдер недоступен.",
      };
    }
    const chart = await this.post("/charts", { action: "candle", symbol, timeframe });
    const payload = (chart.json || {}) as Record<string, unknown>;
    const barsRaw = Array.isArray(payload.bars) ? payload.bars : [];
    return {
      symbol,
      timeframe,
      status: chart.ok ? "connected" : "error",
      providerId: this.id,
      providerLabel: this.label,
      quote: payload.quote
        ? {
            symbol,
            bid: String((payload.quote as Record<string, unknown>).bid ?? "—"),
            ask: String((payload.quote as Record<string, unknown>).ask ?? "—"),
            change: String((payload.quote as Record<string, unknown>).change ?? "—"),
            updatedAt: String((payload.quote as Record<string, unknown>).updated_at ?? ""),
            source: this.label,
          }
        : null,
      freshnessNote: String(payload.freshness || payload.updated_at || "ответ API"),
      bars: barsRaw.map((b) => {
        const row = b as Record<string, unknown>;
        return { t: String(row.t || row.time || ""), c: Number(row.c || row.close || 0) };
      }),
      message: chart.ok ? "Данные от провайдера" : "Ошибка загрузки графика",
    };
  }
}

let activeProvider: MarketChartProvider = new NullChartProvider();

export function setMarketChartProvider(provider: MarketChartProvider) {
  activeProvider = provider;
}

export function getMarketChartProvider(): MarketChartProvider {
  return activeProvider;
}

export const CHART_TIMEFRAMES: ChartTimeframe[] = ["1m", "5m", "15m", "1h", "4h", "1D", "1W"];
