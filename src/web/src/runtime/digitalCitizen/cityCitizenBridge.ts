/**
 * Enterprise City ↔ Digital Citizen facade — Sprint 29.1.
 */

import type {
  CitizenProfile,
  CityCitizenFacade,
  OrganizationMember,
  PersonalAiAgent,
} from "./citizenTypes";

export function toCityCitizenFacade(
  citizen: CitizenProfile,
  membership: OrganizationMember | null,
  ais: PersonalAiAgent[],
): CityCitizenFacade {
  return {
    citizenId: citizen.id,
    displayName: citizen.displayName,
    avatarUrl: citizen.avatarUrl,
    presence: citizen.presence.status,
    role: membership?.role,
    companyOrgId: membership?.orgId || citizen.primaryOrgId,
    companyBusinessProfileId: membership?.businessProfileId,
    officeId: citizen.presence.officeId,
    locationLabel: citizen.presence.locationLabel,
    cityBuildingId: citizen.presence.cityBuildingId,
    aiAssignmentIds: ais
      .filter((a) => a.assignedCitizenId === citizen.id)
      .map((a) => a.id),
  };
}

export const cityCitizenBridge = {
  load(
    citizenId: string,
    citizens: CitizenProfile[],
    memberships: OrganizationMember[],
    ais: PersonalAiAgent[],
  ): CityCitizenFacade | null {
    const c = citizens.find((x) => x.id === citizenId);
    if (!c) return null;
    const membership =
      memberships.find((m) => m.citizenId === citizenId && m.active) ||
      memberships.find((m) => m.citizenId === citizenId) ||
      null;
    return toCityCitizenFacade(c, membership, ais);
  },
};
