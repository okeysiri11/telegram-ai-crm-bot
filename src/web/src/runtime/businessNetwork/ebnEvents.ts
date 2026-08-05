/**
 * EBN event bridge — Sprint 29.0.
 * Publishes Runtime Events on Enterprise EventBus.
 */

import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import type { EbnEventName } from "./ebnTypes";
import { BUSINESS_NETWORK_VERSION } from "./ebnTypes";

export function publishEbnEvent(
  name: EbnEventName,
  payload: Record<string, unknown> = {},
) {
  enterpriseEventBus.publish({
    type: "business_network_update",
    source: "system",
    payload: {
      stream: "business_network",
      event: name,
      version: BUSINESS_NETWORK_VERSION,
      ...payload,
    },
  });
}

export const ebnEvents = {
  partnerAdded: (relationshipId: string, from: string, to: string) =>
    publishEbnEvent("PartnerAdded", { relationshipId, fromProfileId: from, toProfileId: to }),
  partnerRemoved: (relationshipId: string) =>
    publishEbnEvent("PartnerRemoved", { relationshipId }),
  relationshipApproved: (relationshipId: string) =>
    publishEbnEvent("RelationshipApproved", { relationshipId }),
  relationshipRejected: (relationshipId: string) =>
    publishEbnEvent("RelationshipRejected", { relationshipId }),
  businessUpdated: (profileId: string) => publishEbnEvent("BusinessUpdated", { profileId }),
  verificationCompleted: (profileId: string, status: string) =>
    publishEbnEvent("VerificationCompleted", { profileId, status }),
  documentLinked: (documentLinkId: string, relationshipId: string) =>
    publishEbnEvent("DocumentLinked", { documentLinkId, relationshipId }),
  businessStatusChanged: (profileId: string, status: string) =>
    publishEbnEvent("BusinessStatusChanged", { profileId, status }),
  messageSent: (conversationId: string, messageId: string) =>
    publishEbnEvent("MessageSent", { conversationId, messageId }),
  conversationCreated: (conversationId: string) =>
    publishEbnEvent("ConversationCreated", { conversationId }),
};
