/**
 * Business relationships — Sprint 29.0.
 */

import type {
  BusinessRelationship,
  RelationshipHistoryEntry,
  RelationshipState,
  RelationshipType,
  VisibilityScope,
} from "./ebnTypes";
import { canMutateRelationship } from "./ebnPermissions";

const byId = new Map<string, BusinessRelationship>();

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

function hist(action: string, actorId?: string, detail?: string): RelationshipHistoryEntry {
  return {
    id: uid("rh"),
    at: new Date().toISOString(),
    action,
    actorId,
    detail,
  };
}

export const relationshipService = {
  clear() {
    byId.clear();
  },

  list() {
    return [...byId.values()];
  },

  get(id: string) {
    return byId.get(id);
  },

  forProfile(profileId: string) {
    return this.list().filter(
      (r) => r.fromProfileId === profileId || r.toProfileId === profileId,
    );
  },

  create(input: {
    fromProfileId: string;
    toProfileId: string;
    type: RelationshipType;
    permissions?: VisibilityScope[];
    notes?: string;
    actorId?: string;
    actorScopes?: VisibilityScope[];
  }): { ok: boolean; relationship?: BusinessRelationship; error?: string } {
    if (input.fromProfileId === input.toProfileId) {
      return { ok: false, error: "self_relationship_forbidden" };
    }
    if (
      input.actorScopes &&
      !canMutateRelationship(input.actorScopes, "create")
    ) {
      return { ok: false, error: "permission_denied" };
    }
    const existing = this.list().find(
      (r) =>
        r.type === input.type &&
        ((r.fromProfileId === input.fromProfileId && r.toProfileId === input.toProfileId) ||
          (r.fromProfileId === input.toProfileId && r.toProfileId === input.fromProfileId)) &&
        r.state !== "archived" &&
        r.state !== "revoked",
    );
    if (existing) return { ok: false, error: "relationship_exists", relationship: existing };

    const now = new Date().toISOString();
    const relationship: BusinessRelationship = {
      id: uid("rel"),
      fromProfileId: input.fromProfileId,
      toProfileId: input.toProfileId,
      type: input.type,
      state: "pending",
      permissions: input.permissions || ["partners"],
      notes: input.notes,
      createdAt: now,
      updatedAt: now,
      history: [hist("created", input.actorId, input.type)],
    };
    byId.set(relationship.id, relationship);
    return { ok: true, relationship };
  },

  update(
    id: string,
    patch: Partial<Pick<BusinessRelationship, "type" | "notes" | "permissions">>,
    actorId?: string,
  ) {
    const cur = byId.get(id);
    if (!cur) return null;
    const next: BusinessRelationship = {
      ...cur,
      ...patch,
      updatedAt: new Date().toISOString(),
      history: [hist("updated", actorId), ...cur.history].slice(0, 80),
    };
    byId.set(id, next);
    return next;
  },

  setState(
    id: string,
    state: RelationshipState,
    actorId?: string,
  ): BusinessRelationship | null {
    const cur = byId.get(id);
    if (!cur) return null;
    const now = new Date().toISOString();
    const next: BusinessRelationship = {
      ...cur,
      state,
      updatedAt: now,
      approvedAt: state === "approved" ? now : cur.approvedAt,
      rejectedAt: state === "rejected" ? now : cur.rejectedAt,
      history: [hist(state, actorId), ...cur.history].slice(0, 80),
    };
    byId.set(id, next);
    return next;
  },

  approve(id: string, actorId?: string) {
    return this.setState(id, "approved", actorId);
  },

  reject(id: string, actorId?: string) {
    return this.setState(id, "rejected", actorId);
  },

  remove(id: string, actorId?: string) {
    const cur = byId.get(id);
    if (!cur) return false;
    this.setState(id, "revoked", actorId);
    return true;
  },

  delete(id: string) {
    return byId.delete(id);
  },

  history(id: string) {
    return byId.get(id)?.history || [];
  },
};
