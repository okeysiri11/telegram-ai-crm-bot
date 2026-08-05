/**
 * @deprecated Use `event_bus/EventBus` (Enterprise Event Bus) or KernelEventBusAdapter.
 * Kept as a thin re-export for Sprint 1.0 compatibility.
 */
export { EventBus } from "../event_bus/EventBus.js";
export { KernelEventBusAdapter as LegacyKernelEventBridge } from "../event_bus/KernelEventBusAdapter.js";
