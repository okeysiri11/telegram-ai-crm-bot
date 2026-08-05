/**
 * Enterprise communication foundation — Sprint 29.0.
 * Direct / business chat · messages · typing · unread · video-room ready.
 */

import type {
  Conversation,
  ConversationKind,
  ConversationMember,
  Message,
  MessageAttachment,
} from "./ebnTypes";

const conversations = new Map<string, Conversation>();
const messages = new Map<string, Message[]>();

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

export const communicationService = {
  clear() {
    conversations.clear();
    messages.clear();
  },

  listConversations() {
    return [...conversations.values()].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
  },

  getConversation(id: string) {
    return conversations.get(id);
  },

  createConversation(input: {
    kind: ConversationKind;
    title: string;
    memberProfileIds: string[];
    relationshipId?: string;
    ownerProfileId: string;
  }): Conversation {
    const now = new Date().toISOString();
    const members: ConversationMember[] = input.memberProfileIds.map((profileId) => ({
      profileId,
      role: profileId === input.ownerProfileId ? "owner" : "member",
      joinedAt: now,
      lastReadAt: now,
    }));
    const unreadByProfile: Record<string, number> = {};
    for (const m of members) unreadByProfile[m.profileId] = 0;

    const conversation: Conversation = {
      id: uid("conv"),
      kind: input.kind,
      title: input.title,
      relationshipId: input.relationshipId,
      members,
      unreadByProfile,
      typing: {},
      createdAt: now,
      updatedAt: now,
      videoRoomCompatible: true,
    };
    conversations.set(conversation.id, conversation);
    messages.set(conversation.id, []);
    return conversation;
  },

  addMember(conversationId: string, profileId: string, role: ConversationMember["role"] = "member") {
    const c = conversations.get(conversationId);
    if (!c) return null;
    if (c.members.some((m) => m.profileId === profileId)) return c;
    const next: Conversation = {
      ...c,
      members: [...c.members, { profileId, role, joinedAt: new Date().toISOString() }],
      unreadByProfile: { ...c.unreadByProfile, [profileId]: 0 },
      updatedAt: new Date().toISOString(),
    };
    conversations.set(conversationId, next);
    return next;
  },

  sendMessage(input: {
    conversationId: string;
    senderProfileId: string;
    body: string;
    attachments?: MessageAttachment[];
  }): { ok: boolean; message?: Message; error?: string } {
    const c = conversations.get(input.conversationId);
    if (!c) return { ok: false, error: "conversation_not_found" };
    if (!c.members.some((m) => m.profileId === input.senderProfileId)) {
      return { ok: false, error: "not_a_member" };
    }
    const message: Message = {
      id: uid("msg"),
      conversationId: input.conversationId,
      senderProfileId: input.senderProfileId,
      body: input.body,
      attachments: input.attachments || [],
      createdAt: new Date().toISOString(),
    };
    const list = messages.get(input.conversationId) || [];
    list.push(message);
    messages.set(input.conversationId, list);

    const unread = { ...c.unreadByProfile };
    for (const m of c.members) {
      if (m.profileId !== input.senderProfileId) {
        unread[m.profileId] = (unread[m.profileId] || 0) + 1;
      }
    }
    const typing = { ...c.typing };
    delete typing[input.senderProfileId];
    conversations.set(input.conversationId, {
      ...c,
      unreadByProfile: unread,
      typing,
      updatedAt: new Date().toISOString(),
    });

    return { ok: true, message };
  },

  listMessages(conversationId: string, limit = 50) {
    const list = messages.get(conversationId) || [];
    return list.slice(-limit);
  },

  setTyping(conversationId: string, profileId: string, isTyping: boolean) {
    const c = conversations.get(conversationId);
    if (!c) return null;
    const typing = { ...c.typing };
    if (isTyping) typing[profileId] = new Date().toISOString();
    else delete typing[profileId];
    const next = { ...c, typing };
    conversations.set(conversationId, next);
    return next;
  },

  markRead(conversationId: string, profileId: string) {
    const c = conversations.get(conversationId);
    if (!c) return null;
    const members = c.members.map((m) =>
      m.profileId === profileId ? { ...m, lastReadAt: new Date().toISOString() } : m,
    );
    const unreadByProfile = { ...c.unreadByProfile, [profileId]: 0 };
    const next = { ...c, members, unreadByProfile, updatedAt: new Date().toISOString() };
    conversations.set(conversationId, next);
    return next;
  },

  unreadCount(profileId: string) {
    return this.listConversations().reduce((s, c) => s + (c.unreadByProfile[profileId] || 0), 0);
  },
};
