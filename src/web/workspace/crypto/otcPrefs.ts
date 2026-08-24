/**
 * Sprint 50.0 — OTC prefs centered on EUR/USD + DXY.
 */

export type AnalysisConfig = {
  id: string;
  name: string;
  instruments: string[];
  markets: string[];
  frequency: string;
  morningReport: boolean;
  eveningReport: boolean;
  preTradeReport: boolean;
  includeNews: boolean;
  includeTechnical: boolean;
  includeDxy: boolean;
  includeMacro: boolean;
  regions: { fx: boolean; crypto: boolean; us: boolean; europe: boolean; asia: boolean };
  enabled: boolean;
  updatedAt: string;
  lastRun?: string;
  nextRun?: string;
  status?: string;
};

export type SpecialistPref = {
  id: string;
  name: string;
  status: "idle" | "configured" | "needs_config";
  instruments: string[];
  lastReport: string;
  lastResult?: string;
  confidence?: string;
  notes: string;
  enabled?: boolean;
  weight?: number;
};

const ANALYSIS_KEY = "ados_otc_analyses_v51";
const SPEC_KEY = "ados_otc_specialists_v51";
const WATCH_KEY = "ados_otc_watchlist_v51";

function tenantScoped(base: string, tenantId?: string) {
  return tenantId ? `${base}::${tenantId}` : base;
}

export function loadWatchlist(tenantId?: string): string[] {
  try {
    const raw = localStorage.getItem(tenantScoped(WATCH_KEY, tenantId));
    if (raw) return JSON.parse(raw) as string[];
  } catch {
    /* ignore */
  }
  return ["EUR/USD", "DXY"];
}

export function saveWatchlist(pairs: string[], tenantId?: string) {
  localStorage.setItem(tenantScoped(WATCH_KEY, tenantId), JSON.stringify(pairs));
}

export function defaultAnalyses(): AnalysisConfig[] {
  const now = new Date().toISOString();
  return [
    {
      id: "morning",
      name: "Утренний обзор",
      instruments: ["EUR/USD", "DXY"],
      markets: ["FX"],
      frequency: "daily",
      morningReport: true,
      eveningReport: false,
      preTradeReport: false,
      includeNews: true,
      includeTechnical: true,
      includeDxy: true,
      includeMacro: true,
      regions: { fx: true, crypto: false, us: true, europe: true, asia: false },
      enabled: false,
      updatedAt: now,
      status: "По расписанию платформы",
    },
    {
      id: "pre_europe",
      name: "Перед Европой",
      instruments: ["EUR/USD", "DXY"],
      markets: ["FX"],
      frequency: "session",
      morningReport: false,
      eveningReport: false,
      preTradeReport: true,
      includeNews: true,
      includeTechnical: true,
      includeDxy: true,
      includeMacro: true,
      regions: { fx: true, crypto: false, us: false, europe: true, asia: false },
      enabled: true,
      updatedAt: now,
      status: "По расписанию платформы",
    },
    {
      id: "pre_us",
      name: "Перед США",
      instruments: ["EUR/USD", "DXY"],
      markets: ["FX"],
      frequency: "session",
      morningReport: false,
      eveningReport: false,
      preTradeReport: true,
      includeNews: true,
      includeTechnical: true,
      includeDxy: true,
      includeMacro: true,
      regions: { fx: true, crypto: false, us: true, europe: false, asia: false },
      enabled: true,
      updatedAt: now,
      status: "По расписанию платформы",
    },
    {
      id: "pre_trade",
      name: "Перед торговлей",
      instruments: ["EUR/USD", "DXY"],
      markets: ["FX"],
      frequency: "session",
      morningReport: false,
      eveningReport: false,
      preTradeReport: true,
      includeNews: false,
      includeTechnical: true,
      includeDxy: true,
      includeMacro: true,
      regions: { fx: true, crypto: false, us: true, europe: true, asia: false },
      enabled: false,
      updatedAt: now,
      status: "По расписанию платформы",
    },
    {
      id: "event",
      name: "Событийный анализ",
      instruments: ["EUR/USD", "DXY"],
      markets: ["FX", "Macro"],
      frequency: "on_event",
      morningReport: false,
      eveningReport: false,
      preTradeReport: false,
      includeNews: true,
      includeTechnical: false,
      includeDxy: true,
      includeMacro: true,
      regions: { fx: true, crypto: false, us: true, europe: true, asia: false },
      enabled: false,
      updatedAt: now,
      status: "По расписанию платформы",
    },
    {
      id: "evening",
      name: "Вечерний обзор",
      instruments: ["EUR/USD", "DXY"],
      markets: ["FX"],
      frequency: "daily",
      morningReport: false,
      eveningReport: true,
      preTradeReport: false,
      includeNews: true,
      includeTechnical: true,
      includeDxy: true,
      includeMacro: true,
      regions: { fx: true, crypto: false, us: true, europe: true, asia: false },
      enabled: false,
      updatedAt: now,
      status: "По расписанию платформы",
    },
  ];
}

export function loadAnalyses(tenantId?: string): AnalysisConfig[] {
  try {
    const raw = localStorage.getItem(tenantScoped(ANALYSIS_KEY, tenantId));
    if (raw) return JSON.parse(raw) as AnalysisConfig[];
  } catch {
    /* ignore */
  }
  return defaultAnalyses();
}

export function saveAnalyses(items: AnalysisConfig[], tenantId?: string) {
  localStorage.setItem(tenantScoped(ANALYSIS_KEY, tenantId), JSON.stringify(items));
}

export function defaultSpecialists(): SpecialistPref[] {
  return [
    { id: "eurusd_structure", name: "EUR/USD Structure Agent", status: "configured", instruments: ["EUR/USD"], lastReport: "—", notes: "" },
    { id: "dxy", name: "DXY Agent", status: "needs_config", instruments: ["DXY"], lastReport: "—", notes: "Нужен источник DXY" },
    { id: "technical", name: "Technical Agent", status: "configured", instruments: ["EUR/USD", "DXY"], lastReport: "—", notes: "" },
    { id: "macro", name: "Macro Agent", status: "needs_config", instruments: ["EUR/USD", "DXY"], lastReport: "—", notes: "Календарь не подключён" },
    { id: "news", name: "News Agent", status: "needs_config", instruments: ["EUR/USD", "DXY"], lastReport: "—", notes: "Новости не подключены" },
    { id: "europe", name: "Europe Session Agent", status: "configured", instruments: ["EUR/USD"], lastReport: "—", notes: "" },
    { id: "us", name: "US Session Agent", status: "configured", instruments: ["EUR/USD", "DXY"], lastReport: "—", notes: "" },
    { id: "risk", name: "Risk Agent", status: "configured", instruments: ["EUR/USD", "DXY"], lastReport: "—", notes: "" },
    { id: "chief", name: "Chief Analyst", status: "configured", instruments: ["EUR/USD", "DXY"], lastReport: "—", notes: "" },
  ];
}

export function loadSpecialists(tenantId?: string): SpecialistPref[] {
  try {
    const raw = localStorage.getItem(tenantScoped(SPEC_KEY, tenantId));
    if (raw) return JSON.parse(raw) as SpecialistPref[];
  } catch {
    /* ignore */
  }
  return defaultSpecialists();
}

export function saveSpecialists(items: SpecialistPref[], tenantId?: string) {
  localStorage.setItem(tenantScoped(SPEC_KEY, tenantId), JSON.stringify(items));
}


const AGENT_SETTINGS_KEY = "ados_otc_agent_settings_v52";

export type AgentSettingsMap = Record<string, { enabled: boolean; weight: number; instruments: string[] }>;

export function loadAgentSettings(tenantId?: string): AgentSettingsMap {
  try {
    const raw = localStorage.getItem(tenantScoped(AGENT_SETTINGS_KEY, tenantId));
    if (raw) return JSON.parse(raw) as AgentSettingsMap;
  } catch {
    /* ignore */
  }
  return {};
}

export function saveAgentSettings(settings: AgentSettingsMap, tenantId?: string) {
  localStorage.setItem(tenantScoped(AGENT_SETTINGS_KEY, tenantId), JSON.stringify(settings));
}

const CHART_PREFS_KEY = "ados_otc_chart_prefs_v53";

export type ChartInstrumentPrefs = {
  primary: string;
  comparison: string;
  eurusdTf: string;
  dxyTf: string;
};

export function loadChartInstrumentPrefs(tenantId?: string): ChartInstrumentPrefs {
  try {
    const raw = localStorage.getItem(tenantScoped(CHART_PREFS_KEY, tenantId));
    if (raw) return JSON.parse(raw) as ChartInstrumentPrefs;
  } catch {
    /* ignore */
  }
  return { primary: "EUR/USD", comparison: "DXY", eurusdTf: "1h", dxyTf: "1h" };
}

export function saveChartInstrumentPrefs(prefs: ChartInstrumentPrefs, tenantId?: string) {
  localStorage.setItem(tenantScoped(CHART_PREFS_KEY, tenantId), JSON.stringify(prefs));
}
