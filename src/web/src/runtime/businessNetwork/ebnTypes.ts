/**
 * Enterprise Business Network types — Sprint 29.0.
 * Business relationship layer of Enterprise City (not a social network).
 */

export const BUSINESS_NETWORK_VERSION = "29.0";
export const EBN_PERSIST_KEY = "ews_business_network_v1";
export const EBN_API_PREFIX = "/api/enterprise-ebn/v1";

export type BusinessCategory =
  | "technology"
  | "manufacturing"
  | "retail"
  | "finance"
  | "services"
  | "logistics"
  | "healthcare"
  | "other";

export type VerificationStatus = "unverified" | "pending" | "verified" | "rejected" | "expired";

export type BusinessStatus = "active" | "inactive" | "suspended" | "prospect" | "archived";

export type RelationshipType =
  | "friend"
  | "partner"
  | "trusted_partner"
  | "supplier"
  | "client"
  | "dealer"
  | "contractor"
  | "strategic_partner"
  | "internal_organization";

export type RelationshipState = "pending" | "approved" | "rejected" | "revoked" | "archived";

export type VisibilityScope =
  | "public"
  | "friends"
  | "partners"
  | "internal"
  | "private"
  | "enterprise_admin"
  | "organization_owner";

export type DocumentLinkKind =
  | "contract"
  | "certificate"
  | "act"
  | "license"
  | "signed_document"
  | "other";

export type ConversationKind = "direct" | "business";

export type BusinessProfile = {
  id: string;
  companyName: string;
  legalName?: string;
  category: BusinessCategory;
  status: BusinessStatus;
  verificationStatus: VerificationStatus;
  avatarUrl?: string;
  tagline?: string;
  industry?: string;
  headquarters?: string;
  website?: string;
  employeeCount?: number;
  trustLevel: number;
  metadata: Record<string, unknown>;
  visibility: VisibilityScope;
  ownerOrgId: string;
  createdAt: string;
  updatedAt: string;
};

export type CompanyCard = {
  id: string;
  companyName: string;
  category: BusinessCategory;
  status: BusinessStatus;
  verificationStatus: VerificationStatus;
  avatarUrl?: string;
  tagline?: string;
  trustLevel: number;
  relationshipCount: number;
  headquarters?: string;
};

export type BusinessRelationship = {
  id: string;
  fromProfileId: string;
  toProfileId: string;
  type: RelationshipType;
  state: RelationshipState;
  permissions: VisibilityScope[];
  notes?: string;
  createdAt: string;
  updatedAt: string;
  approvedAt?: string;
  rejectedAt?: string;
  history: RelationshipHistoryEntry[];
};

export type RelationshipHistoryEntry = {
  id: string;
  at: string;
  action: string;
  actorId?: string;
  detail?: string;
};

export type GraphNode = {
  id: string;
  profileId: string;
  label: string;
  category: BusinessCategory;
  trustLevel: number;
};

export type GraphEdge = {
  id: string;
  relationshipId: string;
  from: string;
  to: string;
  type: RelationshipType;
  state: RelationshipState;
  weight: number;
};

export type GraphQueryResult = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  path?: string[];
};

export type ConversationMember = {
  profileId: string;
  role: "owner" | "member" | "guest";
  joinedAt: string;
  lastReadAt?: string;
};

export type Conversation = {
  id: string;
  kind: ConversationKind;
  title: string;
  relationshipId?: string;
  members: ConversationMember[];
  unreadByProfile: Record<string, number>;
  typing: Record<string, string>;
  createdAt: string;
  updatedAt: string;
  /** Reserved for future video rooms */
  videoRoomCompatible: boolean;
};

export type MessageAttachment = {
  id: string;
  name: string;
  mimeType: string;
  sizeBytes: number;
  url?: string;
};

export type Message = {
  id: string;
  conversationId: string;
  senderProfileId: string;
  body: string;
  attachments: MessageAttachment[];
  createdAt: string;
  editedAt?: string;
};

export type VerifiedDocumentLink = {
  id: string;
  relationshipId: string;
  kind: DocumentLinkKind;
  title: string;
  documentRef: string;
  verified: boolean;
  linkedAt: string;
  linkedBy?: string;
  metadata: Record<string, unknown>;
};

/** City building runtime interface — no graphics. */
export type CityBusinessFacade = {
  profileId: string;
  companyName: string;
  status: BusinessStatus;
  trustLevel: number;
  relationshipCount: number;
  headquarters?: string;
  verificationStatus: VerificationStatus;
  reputationScore?: number;
};

export type EbnEventName =
  | "PartnerAdded"
  | "PartnerRemoved"
  | "RelationshipApproved"
  | "RelationshipRejected"
  | "BusinessUpdated"
  | "VerificationCompleted"
  | "DocumentLinked"
  | "BusinessStatusChanged"
  | "MessageSent"
  | "ConversationCreated";
