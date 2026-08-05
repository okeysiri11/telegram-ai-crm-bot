/**
 * Verified document links — Sprint 29.0.
 * Associates contracts/certificates/acts/licenses with relationships.
 * OCR intentionally out of scope.
 */

import type { DocumentLinkKind, VerifiedDocumentLink } from "./ebnTypes";

const links = new Map<string, VerifiedDocumentLink>();

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

export const documentLinkService = {
  clear() {
    links.clear();
  },

  list() {
    return [...links.values()];
  },

  forRelationship(relationshipId: string) {
    return this.list().filter((l) => l.relationshipId === relationshipId);
  },

  get(id: string) {
    return links.get(id);
  },

  link(input: {
    relationshipId: string;
    kind: DocumentLinkKind;
    title: string;
    documentRef: string;
    verified?: boolean;
    linkedBy?: string;
    metadata?: Record<string, unknown>;
  }): VerifiedDocumentLink {
    const entry: VerifiedDocumentLink = {
      id: uid("docl"),
      relationshipId: input.relationshipId,
      kind: input.kind,
      title: input.title,
      documentRef: input.documentRef,
      verified: input.verified !== false,
      linkedAt: new Date().toISOString(),
      linkedBy: input.linkedBy,
      metadata: input.metadata || {},
    };
    links.set(entry.id, entry);
    return entry;
  },

  unlink(id: string) {
    return links.delete(id);
  },
};
