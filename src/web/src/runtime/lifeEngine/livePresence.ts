/**
 * Live presence mapping — Sprint 29.2.
 * Bridges Digital Citizen presence → Life presence labels.
 */

import type { LifePresence } from "./lifeTypes";
import type { PresenceStatus } from "@/runtime/digitalCitizen";

export function toLifePresence(status: PresenceStatus | string): LifePresence {
  switch (status) {
    case "working":
      return "working";
    case "meeting":
      return "in_meeting";
    case "busy":
      return "busy";
    case "away":
    case "invisible":
      return "offline";
    case "vacation":
      return "vacation";
    case "online":
      return "available";
    case "offline":
      return "offline";
    default:
      return "available";
  }
}

export function toCitizenPresence(life: LifePresence): PresenceStatus {
  switch (life) {
    case "working":
      return "working";
    case "in_meeting":
      return "meeting";
    case "travelling":
      return "away";
    case "busy":
      return "busy";
    case "available":
      return "online";
    case "remote":
      return "working";
    case "vacation":
      return "vacation";
    case "offline":
      return "offline";
  }
}

export const livePresence = {
  toLifePresence,
  toCitizenPresence,
};
