/**
 * Business interactions — Sprint 29.2.
 * Real visits / meetings / docs over EBN + Citizens.
 */

import type { BusinessInteraction } from "./lifeTypes";
import { publishLifeEvent } from "./lifeEventEngine";

const items: BusinessInteraction[] = [];

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

export const businessInteractions = {
  clear() {
    items.length = 0;
  },

  list(limit = 40) {
    return items.slice(0, limit);
  },

  record(
    kind: BusinessInteraction["kind"],
    partial: Omit<Partial<BusinessInteraction>, "id" | "kind" | "at"> & { detail?: string },
  ): BusinessInteraction {
    const entry: BusinessInteraction = {
      id: uid("bi"),
      kind,
      fromCitizenId: partial.fromCitizenId,
      toCitizenId: partial.toCitizenId,
      companyId: partial.companyId,
      partnerCompanyId: partial.partnerCompanyId,
      buildingId: partial.buildingId,
      projectId: partial.projectId,
      documentRef: partial.documentRef,
      at: new Date().toISOString(),
      detail: partial.detail,
    };
    items.unshift(entry);
    if (items.length > 200) items.length = 200;

    const lifeKind =
      kind === "business_visit"
        ? "business_visit"
        : kind === "meeting_invitation"
          ? "meeting_invitation"
          : kind === "document_exchange"
            ? "document_shared"
            : kind === "partnership_discussion"
              ? "partnership_discussion"
              : kind === "shared_workspace"
                ? "shared_workspace"
                : "project_collaboration";

    publishLifeEvent(lifeKind, {
      citizenId: partial.fromCitizenId,
      companyId: partial.companyId,
      buildingId: partial.buildingId,
      projectId: partial.projectId,
      documentRef: partial.documentRef,
      message: partial.detail,
      payload: {
        interactionId: entry.id,
        partnerCompanyId: partial.partnerCompanyId,
        toCitizenId: partial.toCitizenId,
      },
    });

    if (kind === "business_visit") {
      publishLifeEvent("partner_visited", {
        citizenId: partial.fromCitizenId,
        companyId: partial.partnerCompanyId || partial.companyId,
        buildingId: partial.buildingId,
        payload: { interactionId: entry.id },
      });
      publishLifeEvent("company_visited", {
        citizenId: partial.fromCitizenId,
        companyId: partial.companyId,
        buildingId: partial.buildingId,
        payload: { interactionId: entry.id },
      });
    }

    return entry;
  },
};
