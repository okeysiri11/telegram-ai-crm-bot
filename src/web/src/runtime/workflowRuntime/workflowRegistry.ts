/**
 * Workflow registry — Sprint 28.8.
 */

import type { WorkflowDefinition } from "./workflowTypes";

const byId = new Map<string, WorkflowDefinition>();
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((l) => l());
}

export const workflowRegistry = {
  subscribe(listener: () => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },

  register(def: WorkflowDefinition) {
    byId.set(def.id, def);
    emit();
    return def;
  },

  registerMany(defs: WorkflowDefinition[]) {
    for (const d of defs) this.register(d);
  },

  get(id: string) {
    return byId.get(id);
  },

  list() {
    return [...byId.values()];
  },

  unregister(id: string) {
    const ok = byId.delete(id);
    if (ok) emit();
    return ok;
  },

  clear() {
    byId.clear();
    emit();
  },
};
