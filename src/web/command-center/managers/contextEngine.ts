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
  patch(partial: Partial<ContextState>) {
    state = { ...state, ...partial };
    return this.get();
  },
  pushPage(path: string) {
    const openedPages = [...state.openedPages, path].slice(-20);
    state = { ...state, openedPages, currentModule: path };
    return this.get();
  },
};
