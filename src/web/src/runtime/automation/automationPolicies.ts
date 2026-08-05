/**
 * Automation policies — Sprint 28.9.
 */

import { DEFAULT_POLICY, type AutomationDefinition, type AutomationPolicy, type ErrorPolicy } from "./automationTypes";

export function normalizePolicy(partial?: Partial<AutomationPolicy>): AutomationPolicy {
  return {
    retryCount: Math.max(0, partial?.retryCount ?? DEFAULT_POLICY.retryCount),
    timeoutMs: Math.max(1000, partial?.timeoutMs ?? DEFAULT_POLICY.timeoutMs),
    backoffMs: Math.max(0, partial?.backoffMs ?? DEFAULT_POLICY.backoffMs),
    concurrency: Math.max(1, partial?.concurrency ?? DEFAULT_POLICY.concurrency),
    priority: Math.min(100, Math.max(0, partial?.priority ?? DEFAULT_POLICY.priority)),
    errorPolicy: (partial?.errorPolicy || DEFAULT_POLICY.errorPolicy) as ErrorPolicy,
  };
}

export function validatePolicy(policy: AutomationPolicy): { ok: boolean; errors: string[] } {
  const errors: string[] = [];
  if (policy.retryCount < 0 || policy.retryCount > 20) errors.push("retryCount_out_of_range");
  if (policy.timeoutMs < 1000 || policy.timeoutMs > 600_000) errors.push("timeoutMs_out_of_range");
  if (policy.backoffMs < 0 || policy.backoffMs > 120_000) errors.push("backoffMs_out_of_range");
  if (policy.concurrency < 1 || policy.concurrency > 20) errors.push("concurrency_out_of_range");
  if (policy.priority < 0 || policy.priority > 100) errors.push("priority_out_of_range");
  if (!["fail", "continue", "retry", "skip"].includes(policy.errorPolicy)) {
    errors.push("errorPolicy_invalid");
  }
  return { ok: errors.length === 0, errors };
}

export function validateAutomation(def: AutomationDefinition): { ok: boolean; errors: string[] } {
  const errors: string[] = [];
  if (!def.id?.trim()) errors.push("id_required");
  if (!def.name?.trim()) errors.push("name_required");
  if (!def.workflowId?.trim()) errors.push("workflowId_required");
  if (!def.triggers?.length) errors.push("triggers_required");
  const policy = validatePolicy(def.policy);
  errors.push(...policy.errors);
  for (const t of def.triggers || []) {
    if (t.kind === "schedule" && !(t.scheduleMs && t.scheduleMs > 0)) {
      errors.push("schedule_requires_scheduleMs");
    }
    if (t.kind === "event_bus" && !t.eventType) errors.push("event_bus_requires_eventType");
    if (t.kind === "command" && !t.commandId) errors.push("command_requires_commandId");
    if (t.kind === "webhook" && !t.webhookToken) errors.push("webhook_requires_token");
  }
  return { ok: errors.length === 0, errors };
}

export function computeBackoffDelay(policy: AutomationPolicy, attempt: number): number {
  // Linear backoff with attempt multiplier
  return policy.backoffMs * Math.max(1, attempt);
}
