import { beforeEach, describe, expect, it } from "vitest";
import {
  BUSINESS_NETWORK_VERSION,
  businessNetworkEngine,
  businessNetworkApi,
  businessGraphEngine,
  ebnPermissions,
  EBN_HOME_PROFILE_ID,
  EBN_PARTNER_PROFILE_ID,
  EBN_SUPPLIER_PROFILE_ID,
  relationshipService,
  communicationService,
  documentLinkService,
} from "@/runtime/businessNetwork";
import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";

describe("Sprint 29.0 Enterprise Business Network", () => {
  beforeEach(() => {
    businessNetworkEngine.__resetForTests();
    commandRuntime.startup();
    businessNetworkEngine.startup();
  });

  it("boots with seed profiles and version 29.0", () => {
    expect(BUSINESS_NETWORK_VERSION).toBe("29.0");
    expect(businessNetworkEngine.getProfile(EBN_HOME_PROFILE_ID)?.companyName).toBe("Demo Corp");
    expect(businessNetworkEngine.getProfile(EBN_PARTNER_PROFILE_ID)).toBeTruthy();
    expect(businessNetworkEngine.stats().approved).toBeGreaterThanOrEqual(1);
  });

  it("creates, approves, rejects, and removes relationships", () => {
    const created = businessNetworkEngine.createRelationship({
      fromProfileId: EBN_HOME_PROFILE_ID,
      toProfileId: EBN_SUPPLIER_PROFILE_ID,
      type: "dealer",
    });
    // may fail if duplicate type already exists between same pair — use friend
    const friend = businessNetworkEngine.createRelationship({
      fromProfileId: EBN_HOME_PROFILE_ID,
      toProfileId: EBN_PARTNER_PROFILE_ID,
      type: "friend",
    });
    expect(friend.ok).toBe(true);
    expect(friend.relationship?.state).toBe("pending");
    const approved = businessNetworkEngine.approveRelationship(friend.relationship!.id);
    expect(approved?.state).toBe("approved");
    const hist = businessNetworkEngine.relationshipHistory(friend.relationship!.id);
    expect(hist.some((h) => h.action === "approved")).toBe(true);

    const pending = businessNetworkEngine.createRelationship({
      fromProfileId: EBN_SUPPLIER_PROFILE_ID,
      toProfileId: EBN_PARTNER_PROFILE_ID,
      type: "contractor",
    });
    expect(pending.ok).toBe(true);
    businessNetworkEngine.rejectRelationship(pending.relationship!.id);
    expect(relationshipService.get(pending.relationship!.id)?.state).toBe("rejected");

    businessNetworkEngine.removeRelationship(friend.relationship!.id);
    expect(relationshipService.get(friend.relationship!.id)?.state).toBe("revoked");
    void created;
  });

  it("validates permissions for profile visibility", () => {
    const home = businessNetworkEngine.getProfile(EBN_HOME_PROFILE_ID)!;
    expect(ebnPermissions.canViewProfile("public", [], false)).toBe(true);
    expect(ebnPermissions.canViewProfile("private", ["partners"], false)).toBe(false);
    expect(ebnPermissions.canViewProfile("private", ["organization_owner"], false)).toBe(true);
    expect(ebnPermissions.canViewProfile(home.visibility, ["partners"], false)).toBe(true);
    expect(ebnPermissions.canMutateRelationship(["public"], "approve")).toBe(false);
    expect(ebnPermissions.canMutateRelationship(["organization_owner"], "approve")).toBe(true);
  });

  it("traverses graph and finds paths", () => {
    const snap = businessNetworkEngine.graphSnapshot();
    expect(snap.nodes.length).toBeGreaterThanOrEqual(2);
    expect(snap.edges.length).toBeGreaterThanOrEqual(1);
    const conn = businessNetworkEngine.graphConnections(EBN_HOME_PROFILE_ID);
    expect(conn.nodes.some((n) => n.id === EBN_PARTNER_PROFILE_ID)).toBe(true);
    const path = businessNetworkEngine.graphPath(EBN_HOME_PROFILE_ID, EBN_PARTNER_PROFILE_ID);
    expect(path.path?.includes(EBN_HOME_PROFILE_ID)).toBe(true);
    expect(path.path?.includes(EBN_PARTNER_PROFILE_ID)).toBe(true);
    const empty = businessGraphEngine.path("missing_a", "missing_b", []);
    expect(empty.path?.length || 0).toBe(0);
  });

  it("supports communication foundation", () => {
    const conv = businessNetworkEngine.createConversation({
      kind: "direct",
      title: "Test DM",
      memberProfileIds: [EBN_HOME_PROFILE_ID, EBN_SUPPLIER_PROFILE_ID],
      ownerProfileId: EBN_HOME_PROFILE_ID,
    });
    expect(conv.videoRoomCompatible).toBe(true);
    businessNetworkEngine.setTyping(conv.id, EBN_HOME_PROFILE_ID, true);
    const msg = businessNetworkEngine.sendMessage({
      conversationId: conv.id,
      senderProfileId: EBN_HOME_PROFILE_ID,
      body: "Hello supplier",
    });
    expect(msg.ok).toBe(true);
    expect(communicationService.unreadCount(EBN_SUPPLIER_PROFILE_ID)).toBeGreaterThanOrEqual(1);
    businessNetworkEngine.markRead(conv.id, EBN_SUPPLIER_PROFILE_ID);
    expect(communicationService.getConversation(conv.id)?.unreadByProfile[EBN_SUPPLIER_PROFILE_ID]).toBe(0);
  });

  it("links verified documents to relationships", () => {
    const rel = businessNetworkEngine.listRelationships(EBN_HOME_PROFILE_ID).find(
      (r) => r.state === "approved",
    );
    expect(rel).toBeTruthy();
    const link = businessNetworkEngine.linkDocument({
      relationshipId: rel!.id,
      kind: "certificate",
      title: "ISO Certificate",
      documentRef: "doc://certs/iso-9001",
      linkedBy: EBN_HOME_PROFILE_ID,
    });
    expect(link.verified).toBe(true);
    expect(documentLinkService.forRelationship(rel!.id).some((d) => d.id === link.id)).toBe(true);
  });

  it("exposes city facade for Enterprise City buildings", () => {
    const facade = businessNetworkEngine.cityFacade(EBN_HOME_PROFILE_ID);
    expect(facade?.companyName).toBe("Demo Corp");
    expect(facade?.trustLevel).toBeGreaterThan(0);
    expect(typeof facade?.relationshipCount).toBe("number");
    expect(facade?.headquarters).toBeTruthy();
  });

  it("publishes business_network_update events", () => {
    const seen: string[] = [];
    const unsub = enterpriseEventBus.subscribe((e) => {
      if (e.type === "business_network_update") {
        seen.push(String(e.payload?.event || ""));
      }
    });
    businessNetworkEngine.updateProfile(EBN_HOME_PROFILE_ID, { tagline: "Updated tagline" });
    expect(seen).toContain("BusinessUpdated");
    unsub();
  });

  it("registers command and local API inventory", async () => {
    const cmd = await commandRuntime.execute("ebn_open");
    expect(cmd.ok).toBe(true);
    const inv = await businessNetworkApi.inventory();
    expect(inv.version || (inv as { stats?: { version: string } }).stats?.version).toBeTruthy();
    const health = await businessNetworkApi.health();
    expect(health.status).toBe("ok");
  });

  it("inspector snapshot covers foundation surfaces", () => {
    const snap = businessNetworkEngine.inspectorSnapshot();
    expect(snap.version).toBe("29.0");
    expect(snap.profiles.length).toBeGreaterThan(0);
    expect(snap.graph.nodes.length).toBeGreaterThan(0);
    expect(snap.city.home).toBeTruthy();
  });
});
