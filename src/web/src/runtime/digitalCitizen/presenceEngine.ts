/**
 * Presence engine — Sprint 29.1.
 * Runtime status for City visualization (no rendering).
 */

import type { CitizenPresence, PresenceStatus } from "./citizenTypes";
import { citizenProfileService } from "./citizenProfileService";

export const PRESENCE_STATUSES: PresenceStatus[] = [
  "online",
  "offline",
  "busy",
  "meeting",
  "working",
  "away",
  "vacation",
  "invisible",
];

export const presenceEngine = {
  set(
    citizenId: string,
    status: PresenceStatus,
    extra?: Partial<Omit<CitizenPresence, "status" | "since">>,
  ) {
    if (!PRESENCE_STATUSES.includes(status)) return null;
    return citizenProfileService.setPresence(citizenId, status, extra);
  },

  get(citizenId: string): CitizenPresence | null {
    return citizenProfileService.get(citizenId)?.presence || null;
  },

  /** City-compatible occupancy map */
  snapshot() {
    return citizenProfileService.list().map((c) => ({
      citizenId: c.id,
      displayName: c.displayName,
      status: c.presence.status,
      officeId: c.presence.officeId,
      cityBuildingId: c.presence.cityBuildingId,
      locationLabel: c.presence.locationLabel,
      since: c.presence.since,
    }));
  },

  onlineCount() {
    return this.snapshot().filter((p) =>
      ["online", "busy", "meeting", "working"].includes(p.status),
    ).length;
  },
};
