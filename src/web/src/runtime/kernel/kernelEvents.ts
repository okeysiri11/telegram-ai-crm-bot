/**
 * Kernel events — Sprint 29.9.
 */

import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { KERNEL_RUNTIME_VERSION } from "./KernelVersion";
import type { KernelEventName } from "./kernelTypes";

const log: {
  id: string;
  name: KernelEventName;
  at: string;
  payload: Record<string, unknown>;
}[] = [];

function uid() {
  return `kern_${Math.random().toString(36).slice(2, 10)}`;
}

export function publishKernelEvent(name: KernelEventName, payload: Record<string, unknown> = {}) {
  const entry = {
    id: uid(),
    name,
    at: new Date().toISOString(),
    payload,
  };
  log.unshift(entry);
  if (log.length > 400) log.length = 400;

  enterpriseEventBus.publish({
    type: "kernel_runtime_update",
    source: "system",
    payload: {
      stream: "kernel_runtime",
      event: name,
      version: KERNEL_RUNTIME_VERSION,
      ...payload,
    },
  });
  return entry;
}

export const kernelEvents = {
  clear() {
    log.length = 0;
  },
  list(limit = 40) {
    return log.slice(0, limit);
  },
  publish: publishKernelEvent,
};
