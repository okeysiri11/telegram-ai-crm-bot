/**
 * Automation triggers — Sprint 28.9.
 * Bridges EventBus · Command · Notifications · Workflow completed · Startup.
 */

import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { useNotificationStore } from "@/notifications/notificationStore";
import { automationRegistry } from "./automationRegistry";
import { automationScheduler } from "./automationScheduler";
import type { AutomationTriggerKind } from "./automationTypes";

type FireFn = (
  automationId: string,
  triggerKind: AutomationTriggerKind,
  extra?: Record<string, unknown>,
) => void;

let fire: FireFn | null = null;
let busUnsub: (() => void) | null = null;
let notifUnsub: (() => void) | null = null;
let bound = false;

export const automationTriggers = {
  bind(handler: FireFn) {
    fire = handler;
  },

  /** Attach listeners once. */
  attach() {
    if (bound) return;
    bound = true;

    automationScheduler.setHandler((automationId) => {
      fire?.(automationId, "schedule");
    });

    busUnsub = enterpriseEventBus.subscribe((event) => {
      for (const a of automationRegistry.list()) {
        if (!a.enabled) continue;
        for (const t of a.triggers) {
          if (t.enabled === false) continue;
          if (t.kind === "event_bus" && t.eventType === event.type) {
            fire?.(a.id, "event_bus", { eventType: event.type, payload: event.payload });
          }
          if (
            t.kind === "workflow_completed" &&
            event.type === "workflow_update" &&
            event.payload?.status === "completed"
          ) {
            fire?.(a.id, "workflow_completed", { payload: event.payload });
          }
          if (t.kind === "notification" && event.type === "notification") {
            const title = String(event.payload?.title || "");
            if (!t.notificationMatch || title.toLowerCase().includes(t.notificationMatch.toLowerCase())) {
              fire?.(a.id, "notification", { title });
            }
          }
          if (t.kind === "command" && (event.type === "command.completed" || event.type === "command.started")) {
            // Avoid recursion when Automation Engine itself drove the command / workflow
            if (event.payload?.via === "automation" || event.payload?.stream === "automation") continue;
            const cmdId = String(event.payload?.commandId || event.payload?.action || "");
            if (t.commandId && (cmdId === t.commandId || event.payload?.action === t.commandId)) {
              fire?.(a.id, "command", { commandId: cmdId });
            }
          }
        }
      }
    });

    // Poll notification store lightly for notification triggers (no second bus)
    let lastCount = useNotificationStore.getState().items.length;
    const timer = setInterval(() => {
      const items = useNotificationStore.getState().items;
      if (items.length === lastCount) return;
      const newest = items[0];
      lastCount = items.length;
      if (!newest) return;
      for (const a of automationRegistry.list()) {
        if (!a.enabled) continue;
        for (const t of a.triggers) {
          if (t.kind !== "notification" || t.enabled === false) continue;
          if (
            !t.notificationMatch ||
            newest.title.toLowerCase().includes(t.notificationMatch.toLowerCase())
          ) {
            fire?.(a.id, "notification", { title: newest.title });
          }
        }
      }
    }, 4000);
    notifUnsub = () => clearInterval(timer);

    // Refresh schedules from registry
    this.syncSchedules();
  },

  syncSchedules() {
    automationScheduler.clear();
    for (const a of automationRegistry.list()) {
      if (!a.enabled) continue;
      for (const t of a.triggers) {
        if (t.kind === "schedule" && t.enabled !== false && t.scheduleMs) {
          automationScheduler.register(a.id, t.scheduleMs);
        }
      }
    }
  },

  fireStartup() {
    for (const a of automationRegistry.list()) {
      if (!a.enabled) continue;
      if (a.triggers.some((t) => t.kind === "startup" && t.enabled !== false)) {
        fire?.(a.id, "startup");
      }
    }
  },

  fireShutdown() {
    for (const a of automationRegistry.list()) {
      if (!a.enabled) continue;
      if (a.triggers.some((t) => t.kind === "shutdown" && t.enabled !== false)) {
        fire?.(a.id, "shutdown");
      }
    }
  },

  /** Webhook token match */
  fireWebhook(token: string, payload?: Record<string, unknown>) {
    for (const a of automationRegistry.list()) {
      if (!a.enabled) continue;
      if (a.triggers.some((t) => t.kind === "webhook" && t.webhookToken === token && t.enabled !== false)) {
        fire?.(a.id, "webhook", payload);
      }
    }
  },

  /** Command Runtime trigger */
  fireCommand(commandId: string) {
    for (const a of automationRegistry.list()) {
      if (!a.enabled) continue;
      if (a.triggers.some((t) => t.kind === "command" && t.commandId === commandId && t.enabled !== false)) {
        fire?.(a.id, "command", { commandId });
      }
    }
  },

  /** AI intent keyword match */
  fireAiIntent(utterance: string) {
    const text = utterance.toLowerCase();
    for (const a of automationRegistry.list()) {
      if (!a.enabled) continue;
      if (
        a.triggers.some(
          (t) =>
            t.kind === "ai_intent" &&
            t.enabled !== false &&
            t.intentMatch &&
            text.includes(t.intentMatch.toLowerCase()),
        )
      ) {
        fire?.(a.id, "ai_intent", { utterance });
      }
    }
  },

  detach() {
    busUnsub?.();
    busUnsub = null;
    notifUnsub?.();
    notifUnsub = null;
    automationScheduler.clear();
    bound = false;
  },
};
