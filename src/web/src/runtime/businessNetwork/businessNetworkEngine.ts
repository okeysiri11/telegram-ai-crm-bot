/**
 * Enterprise Business Network Engine — Sprint 29.0.
 * Facade over profile · relationships · graph · communication · documents.
 */

import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { BUSINESS_NETWORK_VERSION } from "./ebnTypes";
import type {
  BusinessCategory,
  BusinessProfile,
  DocumentLinkKind,
  RelationshipType,
  VisibilityScope,
} from "./ebnTypes";
import { businessProfileService } from "./businessProfileService";
import { relationshipService } from "./relationshipService";
import { businessGraphEngine } from "./businessGraphEngine";
import { communicationService } from "./communicationService";
import { documentLinkService } from "./documentLinkService";
import { cityBusinessBridge } from "./cityBusinessBridge";
import { ebnEvents } from "./ebnEvents";
import { ebnPermissions } from "./ebnPermissions";
import { seedBusinessNetwork, EBN_HOME_PROFILE_ID } from "./ebnSeed";

let booted = false;

function registerCommands() {
  commandRuntime.register({
    id: "ebn_open",
    action: "open_business_network",
    label: "Open Business Network",
    kind: "navigate",
    keywords: ["business", "network", "partner", "ebn"],
    route: "/business-network",
    permission: "*",
  });
  commandRuntime.register({
    id: "ebn_create_partner",
    action: "create_partner_relationship",
    label: "Create Partner Relationship",
    kind: "system",
    keywords: ["partner", "relationship", "ebn"],
    permission: "*",
    handler: async (_ctx, args) => {
      const to = String(args.toProfileId || args.to || "");
      const from = String(args.fromProfileId || args.from || EBN_HOME_PROFILE_ID);
      if (!to) return { ok: false, error: "toProfileId_required" };
      const res = businessNetworkEngine.createRelationship({
        fromProfileId: from,
        toProfileId: to,
        type: (args.type as RelationshipType) || "partner",
        actorId: from,
      });
      return { ok: res.ok, message: res.relationship?.id, error: res.error };
    },
  });
}

export const businessNetworkEngine = {
  version: BUSINESS_NETWORK_VERSION,

  startup() {
    if (booted) return this.stats();
    commandRuntime.startup();
    seedBusinessNetwork();
    registerCommands();
    booted = true;
    enterpriseEventBus.publish({
      type: "runtime_update",
      source: "system",
      payload: { stream: "business_network", ready: true, version: BUSINESS_NETWORK_VERSION },
    });
    enterpriseEventBus.publish({
      type: "city_update",
      source: "system",
      payload: {
        stream: "business_network",
        profiles: businessProfileService.list().length,
        relationships: relationshipService.list().filter((r) => r.state === "approved").length,
      },
    });
    return this.stats();
  },

  isReady() {
    return booted;
  },

  /** Profiles */
  createProfile(
    input: Parameters<typeof businessProfileService.upsert>[0],
  ): BusinessProfile {
    this.startup();
    const profile = businessProfileService.upsert(input);
    ebnEvents.businessUpdated(profile.id);
    return profile;
  },

  updateProfile(id: string, patch: Parameters<typeof businessProfileService.update>[1]) {
    this.startup();
    const next = businessProfileService.update(id, patch);
    if (next) {
      ebnEvents.businessUpdated(id);
      if (patch?.status) ebnEvents.businessStatusChanged(id, patch.status);
      if (patch?.verificationStatus) ebnEvents.verificationCompleted(id, patch.verificationStatus);
    }
    return next;
  },

  getProfile(id: string) {
    this.startup();
    return businessProfileService.get(id);
  },

  listProfiles() {
    this.startup();
    return businessProfileService.list();
  },

  companyCard(id: string) {
    this.startup();
    const p = businessProfileService.get(id);
    if (!p) return null;
    const count = relationshipService.forProfile(id).filter((r) => r.state === "approved").length;
    return businessProfileService.toCard(p, count);
  },

  /** Relationships */
  createRelationship(input: {
    fromProfileId: string;
    toProfileId: string;
    type: RelationshipType;
    permissions?: VisibilityScope[];
    notes?: string;
    actorId?: string;
  }) {
    this.startup();
    const res = relationshipService.create({
      ...input,
      actorScopes: ["organization_owner", "partners"],
    });
    if (res.ok && res.relationship) {
      ebnEvents.partnerAdded(res.relationship.id, input.fromProfileId, input.toProfileId);
    }
    return res;
  },

  updateRelationship(
    id: string,
    patch: Parameters<typeof relationshipService.update>[1],
    actorId?: string,
  ) {
    this.startup();
    return relationshipService.update(id, patch, actorId);
  },

  approveRelationship(id: string, actorId?: string) {
    this.startup();
    const r = relationshipService.approve(id, actorId);
    if (r) ebnEvents.relationshipApproved(id);
    return r;
  },

  rejectRelationship(id: string, actorId?: string) {
    this.startup();
    const r = relationshipService.reject(id, actorId);
    if (r) ebnEvents.relationshipRejected(id);
    return r;
  },

  removeRelationship(id: string, actorId?: string) {
    this.startup();
    const ok = relationshipService.remove(id, actorId);
    if (ok) ebnEvents.partnerRemoved(id);
    return ok;
  },

  deleteRelationship(id: string) {
    this.startup();
    const ok = relationshipService.delete(id);
    if (ok) ebnEvents.partnerRemoved(id);
    return ok;
  },

  listRelationships(profileId?: string) {
    this.startup();
    return profileId ? relationshipService.forProfile(profileId) : relationshipService.list();
  },

  relationshipHistory(id: string) {
    return relationshipService.history(id);
  },

  /** Graph */
  graphSnapshot() {
    this.startup();
    return businessGraphEngine.snapshot(
      businessProfileService.list(),
      relationshipService.list(),
    );
  },

  graphConnections(profileId: string) {
    this.startup();
    return businessGraphEngine.connections(
      profileId,
      businessProfileService.list(),
      relationshipService.list(),
    );
  },

  graphTraverse(profileId: string, depth = 2) {
    this.startup();
    return businessGraphEngine.traverse(
      profileId,
      businessProfileService.list(),
      relationshipService.list(),
      depth,
    );
  },

  graphPath(fromId: string, toId: string) {
    this.startup();
    return businessGraphEngine.path(fromId, toId, relationshipService.list());
  },

  /** Communication */
  createConversation(input: Parameters<typeof communicationService.createConversation>[0]) {
    this.startup();
    const c = communicationService.createConversation(input);
    ebnEvents.conversationCreated(c.id);
    return c;
  },

  sendMessage(input: Parameters<typeof communicationService.sendMessage>[0]) {
    this.startup();
    const res = communicationService.sendMessage(input);
    if (res.ok && res.message) ebnEvents.messageSent(input.conversationId, res.message.id);
    return res;
  },

  listConversations() {
    this.startup();
    return communicationService.listConversations();
  },

  listMessages(conversationId: string) {
    return communicationService.listMessages(conversationId);
  },

  setTyping(conversationId: string, profileId: string, isTyping: boolean) {
    return communicationService.setTyping(conversationId, profileId, isTyping);
  },

  markRead(conversationId: string, profileId: string) {
    return communicationService.markRead(conversationId, profileId);
  },

  /** Documents */
  linkDocument(input: {
    relationshipId: string;
    kind: DocumentLinkKind;
    title: string;
    documentRef: string;
    linkedBy?: string;
  }) {
    this.startup();
    const link = documentLinkService.link(input);
    ebnEvents.documentLinked(link.id, input.relationshipId);
    return link;
  },

  listDocumentLinks(relationshipId?: string) {
    this.startup();
    return relationshipId
      ? documentLinkService.forRelationship(relationshipId)
      : documentLinkService.list();
  },

  /** City */
  cityFacade(profileId: string) {
    this.startup();
    const p = businessProfileService.get(profileId);
    if (!p) return null;
    return cityBusinessBridge.loadForBuilding(
      profileId,
      businessProfileService.list(),
      relationshipService.list(),
    );
  },

  cityFacadesForBuildings(buildingToProfile: Record<string, string>) {
    this.startup();
    const out: Record<string, ReturnType<typeof this.cityFacade>> = {};
    for (const [buildingId, profileId] of Object.entries(buildingToProfile)) {
      out[buildingId] = this.cityFacade(profileId);
    }
    return out;
  },

  permissions: ebnPermissions,

  stats() {
    const profiles = businessProfileService.list();
    const rels = relationshipService.list();
    return {
      version: BUSINESS_NETWORK_VERSION,
      profiles: profiles.length,
      relationships: rels.length,
      approved: rels.filter((r) => r.state === "approved").length,
      pending: rels.filter((r) => r.state === "pending").length,
      conversations: communicationService.listConversations().length,
      documents: documentLinkService.list().length,
      categories: [...new Set(profiles.map((p) => p.category as BusinessCategory))].length,
    };
  },

  inspectorSnapshot() {
    this.startup();
    return {
      version: BUSINESS_NETWORK_VERSION,
      profiles: businessProfileService.list(),
      cards: businessProfileService.list().map((p) =>
        businessProfileService.toCard(
          p,
          relationshipService.forProfile(p.id).filter((r) => r.state === "approved").length,
        ),
      ),
      relationships: relationshipService.list(),
      graph: this.graphSnapshot(),
      conversations: communicationService.listConversations(),
      documents: documentLinkService.list(),
      city: {
        home: this.cityFacade(EBN_HOME_PROFILE_ID),
      },
      stats: this.stats(),
    };
  },

  __resetForTests() {
    businessProfileService.clear();
    relationshipService.clear();
    communicationService.clear();
    documentLinkService.clear();
    booted = false;
  },
};
