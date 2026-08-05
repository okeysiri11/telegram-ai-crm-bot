import type { ServiceEndpoint } from "./ServiceEndpoint.js";
import type {
  DiscoveryQuery,
  HeartbeatRecord,
  MeshHealthStatus,
  RouteRequest,
  RouteResult,
  SemVerRange,
  ServiceDependency,
  ServiceDescriptorInit,
  ServiceMeshOptions,
} from "./types.js";
import type { ServiceDescriptor } from "./ServiceDescriptor.js";

/**
 * Mesh-facing service contract (descriptor + optional local invoke).
 * Distinct from kernel lifecycle IService — adapters bridge both.
 */
export interface IMeshRegistrable {
  readonly id: string;
  readonly version: string;
  toDescriptor(): ServiceDescriptor;
}

export interface IServiceDiscovery {
  register(descriptor: ServiceDescriptor | ServiceDescriptorInit): ServiceDescriptor;
  unregister(serviceId: string): boolean;
  discover(query: DiscoveryQuery): readonly ServiceDescriptor[];
  get(serviceId: string): ServiceDescriptor | undefined;
  list(): readonly ServiceDescriptor[];
  clear(): void;
}

export interface IServiceResolver {
  resolveDependencies(
    serviceId: string,
  ): {
    readonly ok: boolean;
    readonly missing: readonly ServiceDependency[];
    readonly resolved: readonly ServiceDescriptor[];
  };
  isCompatible(version: string, range?: SemVerRange): boolean;
  resolveByCapability(
    capability: string,
    range?: SemVerRange,
  ): ServiceDescriptor | undefined;
}

export interface IServiceHealth {
  report(
    serviceId: string,
    status: MeshHealthStatus,
    details?: Record<string, unknown>,
  ): void;
  heartbeat(serviceId: string, status?: MeshHealthStatus): HeartbeatRecord;
  getStatus(serviceId: string): MeshHealthStatus;
  getHeartbeat(serviceId: string): HeartbeatRecord | undefined;
  checkTimeouts(now?: number): readonly string[];
  watch(serviceId: string): void;
  unwatch(serviceId: string): void;
  clear(): void;
}

export interface IServiceRouter {
  route<T = unknown>(request: RouteRequest): Promise<RouteResult<T>>;
  callLocal<T = unknown>(
    serviceId: string,
    method: string,
    input?: unknown,
  ): Promise<RouteResult<T>>;
}

export interface IServiceMesh {
  readonly discovery: IServiceDiscovery;
  readonly resolver: IServiceResolver;
  readonly health: IServiceHealth;
  readonly router: IServiceRouter;

  register(descriptor: ServiceDescriptor | ServiceDescriptorInit): ServiceDescriptor;
  unregister(serviceId: string): boolean;
  discover(query: DiscoveryQuery): readonly ServiceDescriptor[];
  resolve(serviceId: string): ServiceDescriptor;
  route<T = unknown>(request: RouteRequest): Promise<RouteResult<T>>;
  callLocal<T = unknown>(
    serviceId: string,
    method: string,
    input?: unknown,
  ): Promise<RouteResult<T>>;
  call<T = unknown>(
    capabilityOrId: string,
    method: string,
    input?: unknown,
  ): Promise<RouteResult<T>>;
  start(): void;
  stop(): void;
  dispose(): void;
  stats(): {
    services: number;
    healthy: number;
    degraded: number;
    unhealthy: number;
    endpoints: number;
  };
}

export type { ServiceDescriptor, ServiceEndpoint, ServiceMeshOptions };
