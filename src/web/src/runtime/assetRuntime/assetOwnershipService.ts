/**
 * Ownership · transfers · assignments — Sprint 29.3.
 */

import type { AssetOwnership, AssetTransferRecord, EnterpriseAsset } from "./assetTypes";
import { assetRegistry } from "./assetRegistry";
import { publishAssetEvent } from "./assetEvents";
import { assetPermissions } from "./assetPermissions";

const transfers: AssetTransferRecord[] = [];

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

export const assetOwnershipService = {
  clear() {
    transfers.length = 0;
  },

  transfers(limit = 40) {
    return transfers.slice(0, limit);
  },

  transfer(input: {
    assetId: string;
    to: AssetOwnership;
    actorId?: string;
    reason?: string;
    actorScopes?: ReturnType<typeof assetPermissions.scopesForActor>;
  }): { ok: boolean; asset?: EnterpriseAsset; error?: string; transfer?: AssetTransferRecord } {
    const asset = assetRegistry.get(input.assetId);
    if (!asset) return { ok: false, error: "asset_not_found" };
    if (input.actorScopes && !assetPermissions.canTransfer(input.actorScopes)) {
      return { ok: false, error: "permission_denied" };
    }
    const from = { ...asset.ownership };
    const next = assetRegistry.update(input.assetId, { ownership: input.to });
    assetRegistry.setLifecycle(input.assetId, "transferred", input.actorId, input.reason);
    const record: AssetTransferRecord = {
      id: uid("tr"),
      assetId: input.assetId,
      from,
      to: input.to,
      at: new Date().toISOString(),
      actorId: input.actorId,
      reason: input.reason,
    };
    transfers.unshift(record);
    if (transfers.length > 200) transfers.length = 200;
    publishAssetEvent("AssetTransferred", input.assetId, {
      from,
      to: input.to,
      reason: input.reason,
    });
    return { ok: true, asset: next || undefined, transfer: record };
  },

  assign(input: {
    assetId: string;
    citizenId?: string;
    companyId?: string;
    actorId?: string;
    actorScopes?: ReturnType<typeof assetPermissions.scopesForActor>;
  }) {
    const asset = assetRegistry.get(input.assetId);
    if (!asset) return { ok: false as const, error: "asset_not_found" };
    if (input.actorScopes && !assetPermissions.canAssign(input.actorScopes)) {
      return { ok: false as const, error: "permission_denied" };
    }
    const next = assetRegistry.update(input.assetId, {
      assignedCitizenId: input.citizenId,
      assignedCompanyId: input.companyId,
      available: false,
      status: "assigned",
    });
    assetRegistry.setLifecycle(input.assetId, "assigned", input.actorId);
    publishAssetEvent("AssetAssigned", input.assetId, {
      citizenId: input.citizenId,
      companyId: input.companyId,
    });
    return { ok: true as const, asset: next };
  },

  unassign(assetId: string, actorId?: string) {
    const next = assetRegistry.update(assetId, {
      assignedCitizenId: undefined,
      assignedCompanyId: undefined,
      available: true,
      status: "registered",
    });
    if (!next) return null;
    assetRegistry.setLifecycle(assetId, "registered", actorId, "unassigned");
    return next;
  },
};
