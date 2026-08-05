/**
 * Business profile service — Sprint 29.0.
 */

import type {
  BusinessProfile,
  BusinessCategory,
  BusinessStatus,
  CompanyCard,
  VerificationStatus,
  VisibilityScope,
} from "./ebnTypes";
import { canViewProfile, scopesFromRelationships } from "./ebnPermissions";
import type { BusinessRelationship } from "./ebnTypes";

const profiles = new Map<string, BusinessProfile>();

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

export const businessProfileService = {
  clear() {
    profiles.clear();
  },

  upsert(
    input: Omit<BusinessProfile, "createdAt" | "updatedAt" | "trustLevel" | "metadata"> & {
      trustLevel?: number;
      metadata?: Record<string, unknown>;
      createdAt?: string;
      updatedAt?: string;
    },
  ): BusinessProfile {
    const now = new Date().toISOString();
    const prev = profiles.get(input.id);
    const profile: BusinessProfile = {
      id: input.id,
      companyName: input.companyName,
      legalName: input.legalName,
      category: input.category,
      status: input.status,
      verificationStatus: input.verificationStatus,
      avatarUrl: input.avatarUrl,
      tagline: input.tagline,
      industry: input.industry,
      headquarters: input.headquarters,
      website: input.website,
      employeeCount: input.employeeCount,
      trustLevel: input.trustLevel ?? prev?.trustLevel ?? 50,
      metadata: input.metadata ?? prev?.metadata ?? {},
      visibility: input.visibility,
      ownerOrgId: input.ownerOrgId,
      createdAt: prev?.createdAt || input.createdAt || now,
      updatedAt: now,
    };
    profiles.set(profile.id, profile);
    return profile;
  },

  get(id: string) {
    return profiles.get(id);
  },

  list() {
    return [...profiles.values()];
  },

  update(
    id: string,
    patch: Partial<
      Pick<
        BusinessProfile,
        | "companyName"
        | "legalName"
        | "category"
        | "status"
        | "verificationStatus"
        | "avatarUrl"
        | "tagline"
        | "industry"
        | "headquarters"
        | "website"
        | "employeeCount"
        | "trustLevel"
        | "metadata"
        | "visibility"
      >
    >,
  ) {
    const cur = profiles.get(id);
    if (!cur) return null;
    const next = { ...cur, ...patch, updatedAt: new Date().toISOString() };
    profiles.set(id, next);
    return next;
  },

  setStatus(id: string, status: BusinessStatus) {
    return this.update(id, { status });
  },

  setVerification(id: string, verificationStatus: VerificationStatus) {
    return this.update(id, { verificationStatus });
  },

  setAvatar(id: string, avatarUrl: string) {
    return this.update(id, { avatarUrl });
  },

  setCategory(id: string, category: BusinessCategory) {
    return this.update(id, { category });
  },

  toCard(profile: BusinessProfile, relationshipCount: number): CompanyCard {
    return {
      id: profile.id,
      companyName: profile.companyName,
      category: profile.category,
      status: profile.status,
      verificationStatus: profile.verificationStatus,
      avatarUrl: profile.avatarUrl,
      tagline: profile.tagline,
      trustLevel: profile.trustLevel,
      relationshipCount,
      headquarters: profile.headquarters,
    };
  },

  visibleTo(
    profileId: string,
    viewerProfileId: string,
    relationships: BusinessRelationship[],
    viewerExtraScopes: VisibilityScope[] = [],
  ): BusinessProfile | null {
    const p = profiles.get(profileId);
    if (!p) return null;
    const scopes = [
      ...scopesFromRelationships(relationships, viewerProfileId, profileId),
      ...viewerExtraScopes,
    ];
    if (!canViewProfile(p.visibility, scopes, viewerProfileId === profileId)) return null;
    return p;
  },

  createId() {
    return uid("biz");
  },
};
