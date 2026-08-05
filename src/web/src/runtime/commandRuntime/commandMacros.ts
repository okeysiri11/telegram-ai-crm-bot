/**
 * Command macros — Sprint 28.7.
 * record · stop · play · save · delete · rename · favorite
 */

import type { CommandMacro, CommandMacroStep } from "./commandTypes";

export const COMMAND_MACROS_KEY = "ews_cmd_macros_v1";

let recording = false;
let draftSteps: CommandMacroStep[] = [];
let macros: CommandMacro[] = [];
let hydrated = false;

function read(): CommandMacro[] {
  try {
    const raw = localStorage.getItem(COMMAND_MACROS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as CommandMacro[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function write(list: CommandMacro[]) {
  try {
    localStorage.setItem(COMMAND_MACROS_KEY, JSON.stringify(list));
  } catch {
    /* ignore */
  }
}

function hydrate() {
  if (hydrated) return;
  macros = typeof window !== "undefined" ? read() : [];
  hydrated = true;
}

function persist() {
  write(macros);
}

export const commandMacros = {
  hydrate,

  isRecording() {
    return recording;
  },

  draft() {
    return [...draftSteps];
  },

  record() {
    recording = true;
    draftSteps = [];
    return true;
  },

  stop() {
    recording = false;
    return [...draftSteps];
  },

  capture(step: CommandMacroStep) {
    if (!recording) return false;
    if (step.action === "undo" || step.action === "redo" || step.commandId.startsWith("macro_")) {
      return false;
    }
    draftSteps.push(step);
    return true;
  },

  save(name: string, steps?: CommandMacroStep[]): CommandMacro {
    hydrate();
    const now = new Date().toISOString();
    const macro: CommandMacro = {
      id: `macro_${Math.random().toString(36).slice(2, 10)}`,
      name: name.trim() || `Macro ${macros.length + 1}`,
      steps: steps || [...draftSteps],
      favorite: false,
      createdAt: now,
      updatedAt: now,
    };
    macros = [macro, ...macros];
    persist();
    recording = false;
    draftSteps = [];
    return macro;
  },

  list(): CommandMacro[] {
    hydrate();
    return [...macros];
  },

  get(id: string): CommandMacro | undefined {
    hydrate();
    return macros.find((m) => m.id === id);
  },

  delete(id: string) {
    hydrate();
    macros = macros.filter((m) => m.id !== id);
    persist();
    return true;
  },

  rename(id: string, name: string) {
    hydrate();
    macros = macros.map((m) =>
      m.id === id ? { ...m, name: name.trim() || m.name, updatedAt: new Date().toISOString() } : m,
    );
    persist();
    return this.get(id);
  },

  favorite(id: string) {
    hydrate();
    macros = macros.map((m) =>
      m.id === id ? { ...m, favorite: !m.favorite, updatedAt: new Date().toISOString() } : m,
    );
    persist();
    return this.get(id);
  },

  favorites(): CommandMacro[] {
    return this.list().filter((m) => m.favorite);
  },
};
