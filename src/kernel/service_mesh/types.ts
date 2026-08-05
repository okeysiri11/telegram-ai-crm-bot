/**
 * Enterprise Service Mesh types.
 * Provider/plugin ready. No business-module imports.
 */

export type MeshHealthStatus =
  | "healthy"
  | "degraded"
  | "unhealthy"
  | "unknown"
  | "starting"
  | "stopped";

/** Transport — local today; http/grpc reserved for future cluster. */
export type EndpointProtocol = "local" | "http" | "grpc" | "internal";

export type LoadBalanceStrategy =
  | "round-robin"
  | "priority"
  | "random"
  | "first-healthy";

export interface SemVerRange {
  /** Inclusive minimum, e.g. "1.0.0" */
  readonly min?: string;
  /** Exclusive maximum, e.g. "2.0.0" */
  readonly maxExclusive?: string;
  /** Exact pin */
  readonly exact?: string;
}

export interface ServiceDependency {
  readonly serviceId?: string;
  readonly capability?: string;
  readonly version?: SemVerRange;
  readonly optional?: boolean;
}

export interface ServiceEndpointInit {
  readonly id: string;
  readonly protocol?: EndpointProtocol;
  readonly address?: string;
  readonly capabilities?: readonly string[];
  /** Local invoker — never cross business modules; call via mesh only. */
  readonly invoke?: ServiceInvoker;
  readonly weight?: number;
  readonly metadata?: Readonly<Record<string, unknown>>;
}

export type ServiceInvoker = (
  method: string,
  input?: unknown,
) => unknown | Promise<unknown>;

export interface ServiceDescriptorInit {
  readonly id: string;
  readonly name?: string;
  readonly version: string;
  readonly capabilities?: readonly string[];
  readonly tags?: readonly string[];
  readonly priority?: number;
  readonly dependencies?: readonly ServiceDependency[];
  readonly endpoints?: readonly ServiceEndpointInit[];
  readonly owner?: string;
  /** Future cluster node id */
  readonly nodeId?: string;
  readonly metadata?: Readonly<Record<string, unknown>>;
}

export interface DiscoveryQuery {
  readonly id?: string;
  readonly capability?: string;
  readonly tag?: string;
  readonly tags?: readonly string[];
  readonly version?: SemVerRange;
  readonly healthyOnly?: boolean;
  readonly protocol?: EndpointProtocol;
}

export interface RouteRequest {
  readonly capability?: string;
  readonly serviceId?: string;
  readonly method: string;
  readonly input?: unknown;
  readonly version?: SemVerRange;
  readonly tags?: readonly string[];
  readonly preferNodeId?: string;
}

export interface RouteResult<T = unknown> {
  readonly ok: boolean;
  readonly serviceId: string;
  readonly endpointId: string;
  readonly version: string;
  readonly data?: T;
  readonly error?: string;
  readonly failoverCount: number;
}

export interface HeartbeatRecord {
  readonly serviceId: string;
  readonly at: string;
  readonly status: MeshHealthStatus;
  readonly uptimeMs: number;
}

export interface ServicePolicyRule {
  readonly id: string;
  readonly action: "allow" | "deny";
  /** Match capability or service id */
  readonly capability?: string;
  readonly serviceId?: string;
  readonly requiredTags?: readonly string[];
  readonly minPriority?: number;
}

export interface ServiceMeshOptions {
  readonly heartbeatIntervalMs?: number;
  readonly heartbeatTimeoutMs?: number;
  readonly loadBalancer?: LoadBalanceStrategy;
  readonly enableHeartbeats?: boolean;
  readonly policies?: readonly ServicePolicyRule[];
}
