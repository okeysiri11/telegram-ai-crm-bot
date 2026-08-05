import type {
  ProviderCapability,
  ProviderConfiguration,
  ProviderExecuteRequest,
  ProviderExecuteResult,
  ProviderHealth,
  ProviderSnapshot,
} from "../types.js";

/**
 * Unified provider contract — all external AI services go through this.
 */
export interface IProvider {
  readonly id: string;
  readonly name: string;

  connect(): Promise<void>;
  disconnect(): Promise<void>;
  health(): ProviderHealth | Promise<ProviderHealth>;
  execute(request: ProviderExecuteRequest): Promise<ProviderExecuteResult>;
  cancel(requestId?: string): Promise<void>;
  capabilities(): readonly ProviderCapability[];
  configuration(): ProviderConfiguration;
  snapshot(): ProviderSnapshot;
}
