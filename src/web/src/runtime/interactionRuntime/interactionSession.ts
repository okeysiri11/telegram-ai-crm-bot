/**
 * Interaction sessions + history + context store — Sprint 29.6.
 */

import type {
  InteractionContext,
  InteractionHistoryEntry,
  InteractionSession,
  InteractionTarget,
  InteractionEventName,
  InteractionActionId,
} from "./interactionTypes";

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

function now() {
  return new Date().toISOString();
}

function defaultContext(surface: InteractionContext["surface"], actorCitizenId?: string): InteractionContext {
  return {
    actorCitizenId,
    surface,
    selectionIds: [],
    path: "/",
    vars: {},
    updatedAt: now(),
  };
}

const sessions = new Map<string, InteractionSession>();
let activeSessionId: string | null = null;
const history: InteractionHistoryEntry[] = [];

export const interactionSessionStore = {
  clear() {
    sessions.clear();
    activeSessionId = null;
  },

  start(input?: {
    actorCitizenId?: string;
    surface?: InteractionContext["surface"];
  }): InteractionSession {
    const surface = input?.surface || "city";
    const session: InteractionSession = {
      id: uid("isess"),
      actorCitizenId: input?.actorCitizenId,
      surface,
      startedAt: now(),
      active: true,
      context: defaultContext(surface, input?.actorCitizenId),
      selectionMode: "single",
    };
    for (const s of sessions.values()) {
      if (s.active) {
        s.active = false;
        s.endedAt = now();
      }
    }
    sessions.set(session.id, session);
    activeSessionId = session.id;
    return session;
  },

  end(sessionId?: string) {
    const id = sessionId || activeSessionId;
    if (!id) return null;
    const s = sessions.get(id);
    if (!s) return null;
    s.active = false;
    s.endedAt = now();
    if (activeSessionId === id) activeSessionId = null;
    return s;
  },

  active() {
    return activeSessionId ? sessions.get(activeSessionId) : undefined;
  },

  get(id: string) {
    return sessions.get(id);
  },

  list() {
    return [...sessions.values()].sort((a, b) => b.startedAt.localeCompare(a.startedAt));
  },

  patchContext(patch: Partial<InteractionContext>, sessionId?: string) {
    const s = sessionId ? sessions.get(sessionId) : this.active();
    if (!s) return null;
    s.context = {
      ...s.context,
      ...patch,
      vars: { ...s.context.vars, ...(patch.vars || {}) },
      selectionIds: patch.selectionIds || s.context.selectionIds,
      updatedAt: now(),
    };
    return s.context;
  },

  setFocus(target: InteractionTarget | undefined, sessionId?: string) {
    return this.patchContext({ focus: target }, sessionId);
  },
};

export const interactionHistory = {
  clear() {
    history.length = 0;
  },

  push(entry: Omit<InteractionHistoryEntry, "id" | "at"> & { at?: string }) {
    const full: InteractionHistoryEntry = {
      id: uid("ih"),
      at: entry.at || now(),
      ...entry,
    };
    history.unshift(full);
    if (history.length > 500) history.length = 500;
    return full;
  },

  list(limit = 40) {
    return history.slice(0, limit);
  },

  recordEvent(
    event: InteractionEventName | "action" | "search" | "navigate",
    opts: {
      sessionId?: string;
      actionId?: InteractionActionId;
      target?: InteractionTarget;
      result?: InteractionHistoryEntry["result"];
      message?: string;
      payload?: Record<string, unknown>;
    } = {},
  ) {
    return this.push({
      event,
      sessionId: opts.sessionId || interactionSessionStore.active()?.id,
      actionId: opts.actionId,
      target: opts.target,
      result: opts.result,
      message: opts.message,
      payload: opts.payload,
    });
  },
};
