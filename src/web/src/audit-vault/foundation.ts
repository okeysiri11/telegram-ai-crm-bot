/**
 * Immutable Audit Vault — foundation only (Sprint 1.1.1).
 * No full storage implementation. Types + append interface for Roadmap 2.0 vault.
 */

export type AuditVaultRecord = {
  id: string;
  ts: string;
  actor: string;
  action: string;
  resource?: string;
  detail?: string;
  correlationId?: string;
  /** Content hash of previous record — chain integrity (vault phase) */
  prevHash?: string;
  hash?: string;
  /** Soft flag until vault backend exists */
  immutable: boolean;
};

export type AuditVaultAppendInput = Omit<AuditVaultRecord, "id" | "ts" | "immutable" | "hash" | "prevHash"> & {
  id?: string;
};

export interface AuditVaultAdapter {
  readonly name: string;
  append(input: AuditVaultAppendInput): Promise<AuditVaultRecord>;
  list?(limit?: number): Promise<AuditVaultRecord[]>;
}

/** In-memory stub — NOT durable / NOT compliance-grade. */
class MemoryAuditVaultAdapter implements AuditVaultAdapter {
  readonly name = "memory_stub";
  private records: AuditVaultRecord[] = [];

  async append(input: AuditVaultAppendInput): Promise<AuditVaultRecord> {
    const prev = this.records[this.records.length - 1];
    const rec: AuditVaultRecord = {
      id: input.id || `avr_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`,
      ts: new Date().toISOString(),
      actor: input.actor,
      action: input.action,
      resource: input.resource,
      detail: input.detail,
      correlationId: input.correlationId,
      prevHash: prev?.hash,
      hash: undefined,
      immutable: false,
    };
    this.records.push(rec);
    return rec;
  }

  async list(limit = 50): Promise<AuditVaultRecord[]> {
    return this.records.slice(-limit).reverse();
  }
}

let adapter: AuditVaultAdapter = new MemoryAuditVaultAdapter();

export function registerAuditVaultAdapter(next: AuditVaultAdapter): void {
  adapter = next;
}

export function getAuditVaultAdapter(): AuditVaultAdapter {
  return adapter;
}

export async function appendAuditVault(input: AuditVaultAppendInput): Promise<AuditVaultRecord> {
  return adapter.append(input);
}

export const AUDIT_VAULT_FOUNDATION = {
  version: "1.1.1",
  status: "foundation_only",
  guarantees: [] as string[],
  nonGoals: [
    "immutable retention",
    "cryptographic chain verification",
    "compliance export",
    "WORM storage",
  ],
  next: "docs/IMMUTABLE_AUDIT_VAULT_FOUNDATION.md",
};
