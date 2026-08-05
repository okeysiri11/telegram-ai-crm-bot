/**
 * Port for Provider Gateway — Orchestrator never imports provider adapters.
 */
export interface ProviderExecutePortResult {
  readonly requestId: string;
  readonly providerId: string;
  readonly ok: boolean;
  readonly output: unknown;
  readonly error?: string;
  readonly durationMs: number;
}

export interface ProviderGatewayPort {
  execute(input: {
    providerId?: string;
    preferredAlias?: string;
    capability: string;
    payload?: unknown;
  }): Promise<ProviderExecutePortResult>;

  selectProvider(options: {
    preferredId?: string;
    preferredAlias?: string;
    capability?: string;
  }): { id: string; name: string };
}
