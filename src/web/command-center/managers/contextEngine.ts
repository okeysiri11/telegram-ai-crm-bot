import type { ContextState } from "../types";

let state: ContextState = {
  workspace: "default",
  organization: "demo_corp",
  openedPages: [],
  openedDocuments: [],
  recentAiConversations: [],
  currentDashboard: null,
  currentModule: null,
  selectedCustomer: null,
  selectedProject: null,
  activeWorkflow: null,
  role: "owner",
  department: "operations",
  permissions: ["*"],
};

export const contextEngine = {
  get(): ContextState {
    return { ...state, openedPages: [...state.openedPages], permissions: [...state.permissions] };
  },
  pushPage(path: string) {
    if (state.openedPages[state.openedPages.length - 1] === path && state.currentModule === path) {
      return this.get();
    }
    const openedPages = [...state.openedPages, path].slice(-20);
    state = { ...state, openedPages, currentModule: path };
    return this.get();
  },
  patch(partial: Partial<ContextState>) {
    let changed = false;
    for (const key of Object.keys(partial) as (keyof ContextState)[]) {
      if (partial[key] !== undefined && partial[key] !== state[key]) {
        // Arrays/objects: shallow length+first check is enough for our scalar-heavy patches
        const next = partial[key];
        const prev = state[key];
        if (Array.isArray(next) && Array.isArray(prev)) {
          if (
            next.length !== prev.length ||
            next.some((v, i) => v !== prev[i])
          ) {
            changed = true;
            break;
          }
        } else if (next !== prev) {
          changed = true;
          break;
        }
      }
    }
    if (!changed) return this.get();
    state = { ...state, ...partial };
    return this.get();
  },
};
