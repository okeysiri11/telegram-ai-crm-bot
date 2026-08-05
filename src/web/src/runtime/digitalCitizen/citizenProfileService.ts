/**
 * Citizen profile service — Sprint 29.1.
 */

import type {
  CitizenProfile,
  CitizenPreferences,
  CitizenPresence,
  CitizenStatus,
  CitizenVerification,
  CitizenIdentity,
  PresenceStatus,
} from "./citizenTypes";

const byId = new Map<string, CitizenProfile>();

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

const DEFAULT_PREFS: CitizenPreferences = {
  locale: "en",
  timezone: "UTC",
  notifyEmail: true,
  notifyPush: true,
  theme: "system",
};

function defaultPresence(): CitizenPresence {
  return { status: "offline", since: new Date().toISOString() };
}

export const citizenProfileService = {
  clear() {
    byId.clear();
  },

  create(
    input: Partial<Omit<CitizenProfile, "createdAt" | "updatedAt">> & {
      displayName: string;
      identity: CitizenIdentity;
      preferences?: Partial<CitizenPreferences>;
      presence?: Partial<CitizenPresence>;
      metadata?: Record<string, unknown>;
      status?: CitizenStatus;
      verification?: CitizenVerification;
    },
  ): CitizenProfile {
    const now = new Date().toISOString();
    const profile: CitizenProfile = {
      id: input.id || uid("cit"),
      displayName: input.displayName,
      firstName: input.firstName,
      lastName: input.lastName,
      title: input.title,
      avatarUrl: input.avatarUrl,
      bio: input.bio,
      status: input.status || "active",
      verification: input.verification || "unverified",
      identity: input.identity,
      preferences: { ...DEFAULT_PREFS, ...input.preferences },
      presence: { ...defaultPresence(), ...input.presence },
      metadata: input.metadata || {},
      primaryOrgId: input.primaryOrgId,
      createdAt: now,
      updatedAt: now,
    };
    byId.set(profile.id, profile);
    return profile;
  },

  get(id: string) {
    return byId.get(id);
  },

  list() {
    return [...byId.values()];
  },

  update(
    id: string,
    patch: Partial<
      Pick<
        CitizenProfile,
        | "displayName"
        | "firstName"
        | "lastName"
        | "title"
        | "avatarUrl"
        | "bio"
        | "status"
        | "verification"
        | "identity"
        | "preferences"
        | "metadata"
        | "primaryOrgId"
      >
    >,
  ) {
    const cur = byId.get(id);
    if (!cur) return null;
    const next: CitizenProfile = {
      ...cur,
      ...patch,
      preferences: patch.preferences ? { ...cur.preferences, ...patch.preferences } : cur.preferences,
      identity: patch.identity ? { ...cur.identity, ...patch.identity } : cur.identity,
      metadata: patch.metadata ? { ...cur.metadata, ...patch.metadata } : cur.metadata,
      updatedAt: new Date().toISOString(),
    };
    byId.set(id, next);
    return next;
  },

  setAvatar(id: string, avatarUrl: string) {
    return this.update(id, { avatarUrl });
  },

  setStatus(id: string, status: CitizenStatus) {
    return this.update(id, { status });
  },

  setVerification(id: string, verification: CitizenVerification) {
    return this.update(id, { verification });
  },

  setPresence(id: string, status: PresenceStatus, extra?: Partial<CitizenPresence>) {
    const cur = byId.get(id);
    if (!cur) return null;
    const presence: CitizenPresence = {
      ...cur.presence,
      ...extra,
      status,
      since: new Date().toISOString(),
    };
    const next = { ...cur, presence, updatedAt: new Date().toISOString() };
    byId.set(id, next);
    return next;
  },

  setPreferences(id: string, preferences: Partial<CitizenPreferences>) {
    const cur = byId.get(id);
    if (!cur) return null;
    return this.update(id, { preferences: { ...cur.preferences, ...preferences } });
  },
};
