/**
 * EBN seed data — Sprint 29.0.
 */

import { businessProfileService } from "./businessProfileService";
import { relationshipService } from "./relationshipService";
import { communicationService } from "./communicationService";
import { documentLinkService } from "./documentLinkService";

export const EBN_HOME_PROFILE_ID = "biz_demo_corp";
export const EBN_PARTNER_PROFILE_ID = "biz_northwind";
export const EBN_SUPPLIER_PROFILE_ID = "biz_logix";

export function seedBusinessNetwork() {
  if (businessProfileService.get(EBN_HOME_PROFILE_ID)) return;

  businessProfileService.upsert({
    id: EBN_HOME_PROFILE_ID,
    companyName: "Demo Corp",
    legalName: "Demo Corporation LLC",
    category: "technology",
    status: "active",
    verificationStatus: "verified",
    avatarUrl: undefined,
    tagline: "Enterprise AI Operating System tenant",
    industry: "Software",
    headquarters: "Enterprise City · Hub Plaza",
    website: "https://demo.corp",
    employeeCount: 120,
    trustLevel: 82,
    visibility: "partners",
    ownerOrgId: "org_demo_corp",
    metadata: { tenant: "demo-corp", cityBuilding: "hub" },
  });

  businessProfileService.upsert({
    id: EBN_PARTNER_PROFILE_ID,
    companyName: "Northwind Partners",
    category: "services",
    status: "active",
    verificationStatus: "verified",
    tagline: "Strategic consulting partner",
    headquarters: "Partner District (planned)",
    trustLevel: 74,
    visibility: "partners",
    ownerOrgId: "org_northwind",
    metadata: { cityBuilding: "marketplace" },
  });

  businessProfileService.upsert({
    id: EBN_SUPPLIER_PROFILE_ID,
    companyName: "LogiX Supply",
    category: "logistics",
    status: "active",
    verificationStatus: "pending",
    tagline: "Regional logistics supplier",
    headquarters: "Logistics Corridor",
    trustLevel: 61,
    visibility: "partners",
    ownerOrgId: "org_logix",
    metadata: {},
  });

  const partner = relationshipService.create({
    fromProfileId: EBN_HOME_PROFILE_ID,
    toProfileId: EBN_PARTNER_PROFILE_ID,
    type: "strategic_partner",
    permissions: ["partners"],
    actorId: EBN_HOME_PROFILE_ID,
    actorScopes: ["organization_owner"],
    notes: "Seed strategic partnership",
  });
  if (partner.relationship) {
    relationshipService.approve(partner.relationship.id, EBN_PARTNER_PROFILE_ID);
    documentLinkService.link({
      relationshipId: partner.relationship.id,
      kind: "contract",
      title: "Master Services Agreement 2026",
      documentRef: "doc://contracts/msa-2026-northwind",
      verified: true,
      linkedBy: EBN_HOME_PROFILE_ID,
    });
  }

  const supplier = relationshipService.create({
    fromProfileId: EBN_HOME_PROFILE_ID,
    toProfileId: EBN_SUPPLIER_PROFILE_ID,
    type: "supplier",
    permissions: ["partners"],
    actorId: EBN_HOME_PROFILE_ID,
    actorScopes: ["organization_owner"],
  });
  if (supplier.relationship) {
    relationshipService.approve(supplier.relationship.id, EBN_HOME_PROFILE_ID);
  }

  const conv = communicationService.createConversation({
    kind: "business",
    title: "Demo Corp ↔ Northwind",
    memberProfileIds: [EBN_HOME_PROFILE_ID, EBN_PARTNER_PROFILE_ID],
    relationshipId: partner.relationship?.id,
    ownerProfileId: EBN_HOME_PROFILE_ID,
  });
  communicationService.sendMessage({
    conversationId: conv.id,
    senderProfileId: EBN_HOME_PROFILE_ID,
    body: "Welcome to the Enterprise Business Network foundation.",
  });
}
