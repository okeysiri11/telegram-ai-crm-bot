import { create } from "zustand";

export type Workspace = {
  company: string;
  department: string;
  project: string;
  userContext: string;
  permissions: string[];
  activeModules: string[];
};

type WorkspaceState = {
  workspace: Workspace;
  setWorkspace: (patch: Partial<Workspace>) => void;
};

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  workspace: {
    company: "demo-corp",
    department: "operations",
    project: "enterprise-web",
    userContext: "owner",
    permissions: ["read", "write", "admin"],
    activeModules: ["hub", "workflow", "ai", "knowledge", "marketplace"],
  },
  setWorkspace: (patch) => {
    const cur = get().workspace;
    let changed = false;
    for (const key of Object.keys(patch) as (keyof Workspace)[]) {
      if (patch[key] !== undefined && patch[key] !== cur[key]) {
        changed = true;
        break;
      }
    }
    if (!changed) return;
    set({ workspace: { ...cur, ...patch } });
  },
}));
