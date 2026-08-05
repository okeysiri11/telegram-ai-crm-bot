/**
 * Provider Gateway types — no real API keys; mock adapters only.
 */

export type ProviderConnectionStatus =
  | "disconnected"
  | "connecting"
  | "connected"
  | "error";

export type ProviderHealthStatus = "OK" | "DEGRADED" | "DOWN";

export interface ProviderCapability {
  readonly id: string;
  readonly description: string;
}

export interface ProviderConfiguration {
  readonly id: string;
  readonly name: string;
  readonly kind: string;
  readonly mock: true;
  readonly baseUrl?: string;
  readonly models?: readonly string[];
  readonly region?: string;
  readonly notes?: string;
}

export interface ProviderHealth {
  readonly status: ProviderHealthStatus;
  readonly message?: string;
  readonly checkedAt: string;
  readonly latencyMs?: number;
}

export interface ProviderExecuteRequest {
  readonly requestId: string;
  readonly capability: string;
  readonly input: unknown;
  readonly providerId?: string;
}

export interface ProviderExecuteResult {
  readonly requestId: string;
  readonly providerId: string;
  readonly ok: boolean;
  readonly output: unknown;
  readonly error?: string;
  readonly durationMs: number;
  readonly completedAt: string;
}

export interface ProviderMetrics {
  readonly totalRequests: number;
  readonly successes: number;
  readonly errors: number;
  readonly avgResponseTimeMs: number;
  readonly currentRequests: number;
  readonly load: number;
}

export interface ProviderSnapshot {
  readonly id: string;
  readonly name: string;
  readonly status: ProviderConnectionStatus;
  readonly connected: boolean;
  readonly health: ProviderHealth;
  readonly capabilities: readonly ProviderCapability[];
  readonly currentRequests: number;
  readonly averageResponseTimeMs: number;
  readonly totalRequests: number;
  readonly errors: number;
  readonly metrics: ProviderMetrics;
  readonly configuration: ProviderConfiguration;
}

export interface GatewayStatus {
  readonly id: "ados.provider_gateway";
  readonly name: "Provider Gateway";
  readonly health: ProviderHealthStatus;
  readonly providers: number;
  readonly connected: number;
  readonly activeConnections: number;
  readonly currentRequests: number;
}

export type ProviderEventType =
  | "provider.connected"
  | "provider.disconnected"
  | "provider.health"
  | "provider.execution"
  | "provider.error";
