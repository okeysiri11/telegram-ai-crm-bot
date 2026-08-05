/**
 * Automation registry — Sprint 28.9.
 */

import type { AutomationDefinition } from "./automationTypes";
import { normalizePolicy, validateAutomation } from "./automationPolicies";

const byId = new Map<string, AutomationDefinition>();
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((l) => l());
}

export const automationRegistry = {
  subscribe(listener: () => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },

  register(input: Omit<AutomationDefinition, "createdAt" | "updatedAt" | "policy"> & {
    policy?: Partial<AutomationDefinition["policy"]>;
    createdAt?: string;
    updatedAt?: string;
  }): { ok: boolean; automation?: AutomationDefinition; errors?: string[] } {
    const now = new Date().toISOString();
    const automation: AutomationDefinition = {
      id: input.id,
      name: input.name,
      description: input.description,
      workflowId: input.workflowId,
      triggers: input.triggers,
      policy: normalizePolicy(input.policy),
      enabled: input.enabled !== false,
      tags: input.tags,
      createdAt: input.createdAt || byId.get(input.id)?.createdAt || now,
      updatedAt: now,
    };
    const v = validateAutomation(automation);
    if (!v.ok) return { ok: false, errors: v.errors };
    byId.set(automation.id, automation);
    emit();
    return { ok: true, automation };
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

  setEnabled(id: string, enabled: boolean) {
    const a = byId.get(id);
    if (!a) return false;
    byId.set(id, { ...a, enabled, updatedAt: new Date().toISOString() });
    emit();
    return true;
  },

  clear() {
    byId.clear();
    emit();
  },
};
