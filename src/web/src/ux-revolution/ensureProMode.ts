/**
 * Sprint 33.1 — switch to Pro Mode with user-visible toast (AI nav / role homes).
 */

import { useExperienceModeStore } from "./experienceModeStore";
import { useNotificationStore } from "@/notifications/notificationStore";

export function ensureProMode(reason = "Switched to Pro Mode"): boolean {
  const store = useExperienceModeStore.getState();
  if (store.mode === "pro") return false;
  store.setMode("pro");
  useNotificationStore.getState().push({
    kind: "toast",
    level: "info",
    title: reason,
    body: "Полная навигация платформы доступна",
  });
  return true;
}
