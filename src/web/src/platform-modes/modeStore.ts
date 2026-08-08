/**
 * Epic 45.1 — Dual Experience mode store (Human / AI / Voice).
 * Only one mode active. Local-first with optional API sync.
 */

import { create } from "zustand";

export type WorkMode = "human" | "ai" | "voice";

export type ModeSettings = {
  remember_last_mode: boolean;
  start_in_human: boolean;
  start_in_ai: boolean;
  start_voice_after_login: boolean;
  require_confirmation: boolean;
  show_execution_plan: boolean;
  speak_answers: boolean;
  show_agents: boolean;
  show_cost: boolean;
  show_duration: boolean;
  default_mode: WorkMode;
};

export const MODE_STORAGE_KEY = "ados_work_mode_v45_1";

export const MODE_INDICATORS: Record<WorkMode, string> = {
  human: "⚪ HUMAN MODE",
  ai: "🟢 AI ACTIVE",
  voice: "🎙 VOICE ACTIVE",
};

export const DEFAULT_MODE_SETTINGS: ModeSettings = {
  remember_last_mode: true,
  start_in_human: true,
  start_in_ai: false,
  start_voice_after_login: false,
  require_confirmation: true,
  show_execution_plan: true,
  speak_answers: true,
  show_agents: true,
  show_cost: true,
  show_duration: true,
  default_mode: "human",
};

function readStored(): { mode: WorkMode; settings: ModeSettings } {
  try {
    const raw = localStorage.getItem(MODE_STORAGE_KEY);
    if (!raw) return { mode: "human", settings: DEFAULT_MODE_SETTINGS };
    const parsed = JSON.parse(raw) as { mode?: WorkMode; settings?: Partial<ModeSettings> };
    const mode: WorkMode =
      parsed.mode === "ai" || parsed.mode === "voice" || parsed.mode === "human"
        ? parsed.mode
        : "human";
    return {
      mode,
      settings: { ...DEFAULT_MODE_SETTINGS, ...(parsed.settings || {}) },
    };
  } catch {
    return { mode: "human", settings: DEFAULT_MODE_SETTINGS };
  }
}

function persist(mode: WorkMode, settings: ModeSettings) {
  try {
    localStorage.setItem(MODE_STORAGE_KEY, JSON.stringify({ mode, settings }));
  } catch {
    /* ignore */
  }
}

type ModeState = {
  mode: WorkMode;
  settings: ModeSettings;
  indicator: string;
  setMode: (mode: WorkMode, channel?: string) => void;
  setVoice: (enabled: boolean) => void;
  updateSettings: (patch: Partial<ModeSettings>) => void;
  rememberDefault: () => void;
  restore: () => void;
  syncFromApi: (ownerId?: string) => Promise<void>;
  pushToApi: (ownerId?: string) => Promise<void>;
  isHuman: () => boolean;
  isAi: () => boolean;
  isVoice: () => boolean;
  canAutoAgents: () => boolean;
};

const initial = typeof window !== "undefined" ? readStored() : { mode: "human" as WorkMode, settings: DEFAULT_MODE_SETTINGS };

export const useModeStore = create<ModeState>((set, get) => ({
  mode: initial.mode,
  settings: initial.settings,
  indicator: MODE_INDICATORS[initial.mode],
  setMode: (mode, channel = "web") => {
    if (mode !== "human" && mode !== "ai" && mode !== "voice") return;
    const settings = get().settings;
    const nextSettings =
      settings.remember_last_mode ? { ...settings, default_mode: mode } : settings;
    persist(mode, nextSettings);
    set({ mode, settings: nextSettings, indicator: MODE_INDICATORS[mode] });
    void fetch("/api/v1/mode/change", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode, channel }),
    }).catch(() => undefined);
  },
  setVoice: (enabled) => {
    get().setMode(enabled ? "voice" : "human", "web");
  },
  updateSettings: (patch) => {
    const settings = { ...get().settings, ...patch };
    persist(get().mode, settings);
    set({ settings });
    void fetch("/api/v1/mode/settings", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    }).catch(() => undefined);
  },
  rememberDefault: () => {
    const { mode, settings } = get();
    const next = { ...settings, default_mode: mode, remember_last_mode: true };
    persist(mode, next);
    set({ settings: next });
    void fetch("/api/v1/mode/remember", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode }),
    }).catch(() => undefined);
  },
  restore: () => {
    const { settings } = get();
    let mode: WorkMode = settings.default_mode || "human";
    if (settings.remember_last_mode && settings.default_mode) mode = settings.default_mode;
    else if (settings.start_in_ai) mode = "ai";
    else if (settings.start_voice_after_login) mode = "voice";
    else if (settings.start_in_human) mode = "human";
    persist(mode, settings);
    set({ mode, indicator: MODE_INDICATORS[mode] });
  },
  syncFromApi: async (ownerId) => {
    try {
      const q = ownerId ? `?owner_id=${encodeURIComponent(ownerId)}` : "";
      const res = await fetch(`/api/v1/mode/status${q}`, { credentials: "include" });
      if (!res.ok) return;
      const json = await res.json();
      const data = json.data || json;
      const mode = (data.mode as WorkMode) || "human";
      const settings = { ...DEFAULT_MODE_SETTINGS, ...(data.settings || {}) };
      persist(mode, settings);
      set({ mode, settings, indicator: MODE_INDICATORS[mode] || data.indicator });
    } catch {
      /* offline — keep local */
    }
  },
  pushToApi: async () => {
    const { mode } = get();
    try {
      await fetch("/api/v1/mode/change", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode, channel: "web" }),
      });
    } catch {
      /* ignore */
    }
  },
  isHuman: () => get().mode === "human",
  isAi: () => get().mode === "ai",
  isVoice: () => get().mode === "voice",
  canAutoAgents: () => get().mode === "ai" || get().mode === "voice",
}));
