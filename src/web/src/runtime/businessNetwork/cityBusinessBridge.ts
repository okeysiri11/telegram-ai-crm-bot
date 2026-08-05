/**
 * Enterprise City ↔ EBN facade — Sprint 29.0.
 * Runtime interfaces only (no graphics).
 */

import type { CityBusinessFacade, BusinessProfile, BusinessRelationship } from "./ebnTypes";

export function toCityBusinessFacade(
  profile: BusinessProfile,
  relationships: BusinessRelationship[],
): CityBusinessFacade {
  const relationshipCount = relationships.filter(
    (r) =>
      (r.fromProfileId === profile.id || r.toProfileId === profile.id) &&
      r.state === "approved",
  ).length;
  return {
    profileId: profile.id,
    companyName: profile.companyName,
    status: profile.status,
    trustLevel: profile.trustLevel,
    relationshipCount,
    headquarters: profile.headquarters,
    verificationStatus: profile.verificationStatus,
    reputationScore: Math.min(100, Math.round(profile.trustLevel * 0.7 + relationshipCount * 3)),
  };
}

export const cityBusinessBridge = {
  /** Load facade for a City building that maps to a business profile id. */
  loadForBuilding(
    buildingBusinessProfileId: string | undefined,
    profiles: BusinessProfile[],
    relationships: BusinessRelationship[],
  ): CityBusinessFacade | null {
    if (!buildingBusinessProfileId) return null;
    const profile = profiles.find((p) => p.id === buildingBusinessProfileId);
    if (!profile) return null;
    return toCityBusinessFacade(profile, relationships);
  },

  /** Batch facades for map overlays. */
  loadMany(
    profileIds: string[],
    profiles: BusinessProfile[],
    relationships: BusinessRelationship[],
  ): CityBusinessFacade[] {
    return profileIds
      .map((id) => {
        const p = profiles.find((x) => x.id === id);
        return p ? toCityBusinessFacade(p, relationships) : null;
      })
      .filter((x): x is CityBusinessFacade => Boolean(x));
  },
};
